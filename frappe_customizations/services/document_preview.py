"""
Document Preview Service using LibreOffice for conversion.

Converts office documents (DOCX, XLSX, PPTX, etc.) to PDF for preview.
"""
import os
import subprocess
import tempfile
import hashlib
import frappe
from frappe.utils import get_files_path


# Supported file extensions for LibreOffice conversion
SUPPORTED_EXTENSIONS = {
    # Word documents
    "doc", "docx", "odt", "rtf",
    # Spreadsheets
    "xls", "xlsx", "ods", "csv",
    # Presentations
    "ppt", "pptx", "odp",
}


def get_preview_cache_path():
    """Get the path where preview PDFs are cached."""
    site_path = frappe.get_site_path("private", "document_previews")
    if not os.path.exists(site_path):
        os.makedirs(site_path, exist_ok=True)
    return site_path


def get_cached_preview(file_hash: str) -> str | None:
    """Check if a preview already exists for this file hash."""
    cache_path = get_preview_cache_path()
    pdf_path = os.path.join(cache_path, f"{file_hash}.pdf")
    if os.path.exists(pdf_path):
        return pdf_path
    return None


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of file for caching."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()[:16]  # Use first 16 chars for filename


def convert_to_pdf(source_path: str, file_hash: str) -> str:
    """
    Convert a document to PDF using LibreOffice.

    Args:
        source_path: Path to the source document
        file_hash: Hash of the file for caching

    Returns:
        Path to the generated PDF file
    """
    cache_path = get_preview_cache_path()
    output_pdf = os.path.join(cache_path, f"{file_hash}.pdf")

    # Check if already cached
    if os.path.exists(output_pdf):
        return output_pdf

    # Use a temp directory for LibreOffice output
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Run LibreOffice in headless mode to convert to PDF
            result = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", temp_dir,
                    source_path
                ],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            if result.returncode != 0:
                frappe.log_error(
                    title="LibreOffice Conversion Failed",
                    message=f"stdout: {result.stdout}\nstderr: {result.stderr}"
                )
                frappe.throw("Failed to convert document to PDF")

            # Find the generated PDF in temp directory
            source_basename = os.path.splitext(os.path.basename(source_path))[0]
            temp_pdf = os.path.join(temp_dir, f"{source_basename}.pdf")

            if not os.path.exists(temp_pdf):
                frappe.throw("PDF conversion completed but output file not found")

            # Move to cache location
            os.rename(temp_pdf, output_pdf)

            return output_pdf

        except subprocess.TimeoutExpired:
            frappe.throw("Document conversion timed out")
        except Exception as e:
            frappe.log_error(title="Document Preview Error", message=str(e))
            raise


def is_supported_format(file_name: str) -> bool:
    """Check if file format is supported for preview."""
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    return ext in SUPPORTED_EXTENSIONS


@frappe.whitelist()
def get_document_preview(file_url: str = None, file_name: str = None):
    """
    Get a PDF preview URL for a document.

    Args:
        file_url: URL of the file (from File doctype)
        file_name: Name of the File doctype record

    Returns:
        dict with preview_url or error
    """
    if not file_url and not file_name:
        frappe.throw("Either file_url or file_name is required")

    # Get file details
    if file_name:
        file_doc = frappe.get_doc("File", file_name)
        file_url = file_doc.file_url

    # Check if format is supported
    if not is_supported_format(file_url):
        return {"supported": False, "message": "File format not supported for preview"}

    # Get the actual file path
    if file_url.startswith("/private/"):
        file_path = frappe.get_site_path(file_url.lstrip("/"))
    elif file_url.startswith("/files/"):
        file_path = frappe.get_site_path("public", file_url.lstrip("/"))
    else:
        frappe.throw("Invalid file URL format")

    if not os.path.exists(file_path):
        frappe.throw("File not found")

    # Compute hash and check cache
    file_hash = compute_file_hash(file_path)
    cached = get_cached_preview(file_hash)

    if cached:
        # Return cached preview URL
        preview_url = f"/api/method/frappe_customizations.services.document_preview.serve_preview?hash={file_hash}"
        return {"supported": True, "preview_url": preview_url}

    # Convert to PDF
    try:
        pdf_path = convert_to_pdf(file_path, file_hash)
        preview_url = f"/api/method/frappe_customizations.services.document_preview.serve_preview?hash={file_hash}"
        return {"supported": True, "preview_url": preview_url}
    except Exception as e:
        return {"supported": False, "message": str(e)}


@frappe.whitelist(allow_guest=False)
def serve_preview(hash: str):
    """Serve a cached PDF preview file."""
    if not hash or len(hash) != 16 or not hash.isalnum():
        frappe.throw("Invalid preview hash")

    cache_path = get_preview_cache_path()
    pdf_path = os.path.join(cache_path, f"{hash}.pdf")

    if not os.path.exists(pdf_path):
        frappe.throw("Preview not found")

    # Read and return the PDF
    with open(pdf_path, "rb") as f:
        pdf_content = f.read()

    frappe.local.response.filename = "preview.pdf"
    frappe.local.response.filecontent = pdf_content
    frappe.local.response.type = "download"
    frappe.local.response.display_content_as = "inline"


@frappe.whitelist()
def convert_drive_file(entity_name: str):
    """
    Convert a Drive File to PDF for preview.

    This is called by the Drive frontend to convert Office documents
    to PDF using LibreOffice instead of Microsoft's external service.

    Args:
        entity_name: The Drive File entity name

    Returns:
        dict with success status and pdf_url or error message
    """
    try:
        # Get the Drive File document
        drive_file = frappe.get_doc("Drive File", entity_name)

        # Check permissions
        if not frappe.has_permission("Drive File", "read", drive_file):
            return {"success": False, "error": "Permission denied"}

        # Get the file path
        file_path = drive_file.path
        if not file_path:
            return {"success": False, "error": "File path not found"}

        # Make path absolute if needed
        if not os.path.isabs(file_path):
            file_path = frappe.get_site_path(file_path)

        if not os.path.exists(file_path):
            return {"success": False, "error": "File not found on disk"}

        # Check if format is supported
        if not is_supported_format(drive_file.title or file_path):
            return {"success": False, "error": "File format not supported for conversion"}

        # Compute hash and convert
        file_hash = compute_file_hash(file_path)

        # Check cache first
        cached = get_cached_preview(file_hash)
        if cached:
            pdf_url = f"/api/method/frappe_customizations.services.document_preview.serve_preview?hash={file_hash}"
            return {"success": True, "pdf_url": pdf_url}

        # Convert to PDF
        convert_to_pdf(file_path, file_hash)
        pdf_url = f"/api/method/frappe_customizations.services.document_preview.serve_preview?hash={file_hash}"
        return {"success": True, "pdf_url": pdf_url}

    except Exception as e:
        frappe.log_error(title="Drive File Conversion Error", message=str(e))
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def cleanup_old_previews(days: int = 7):
    """
    Clean up preview files older than specified days.
    Run this as a scheduled task.
    """
    import time

    cache_path = get_preview_cache_path()
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    removed_count = 0

    for filename in os.listdir(cache_path):
        if not filename.endswith(".pdf"):
            continue

        file_path = os.path.join(cache_path, filename)
        if os.path.getmtime(file_path) < cutoff_time:
            os.remove(file_path)
            removed_count += 1

    return {"removed": removed_count}
