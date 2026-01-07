"""
Apply Drive frontend patches.

This script copies patched Vue components to the Drive app and rebuilds the frontend.
Run this after installing/updating the Drive app.

Usage:
    bench execute frappe_customizations.drive_patches.apply_patches.apply_all

Or from command line:
    bench --site <site> execute frappe_customizations.drive_patches.apply_patches.apply_all
"""
import os
import shutil
import subprocess
import frappe


def get_patches_dir():
    """Get the directory containing patch files."""
    return os.path.dirname(os.path.abspath(__file__))


def get_drive_frontend_dir():
    """Get the Drive app frontend components directory."""
    # frappe.get_app_path returns /apps/drive/drive, we need /apps/drive/frontend
    drive_module_path = frappe.get_app_path("drive")
    drive_app_path = os.path.dirname(drive_module_path)  # Go up to /apps/drive
    return os.path.join(drive_app_path, "frontend", "src", "components", "FileTypePreview")


def apply_vue_patches():
    """Copy patched Vue components to Drive app."""
    patches_dir = get_patches_dir()
    drive_preview_dir = get_drive_frontend_dir()

    if not os.path.exists(drive_preview_dir):
        frappe.throw(f"Drive FileTypePreview directory not found: {drive_preview_dir}")

    patches = [
        "MSOfficePreview.vue",
        "PDFPreview.vue",
    ]

    applied = []
    for patch_file in patches:
        src = os.path.join(patches_dir, patch_file)
        dst = os.path.join(drive_preview_dir, patch_file)

        if os.path.exists(src):
            shutil.copy2(src, dst)
            applied.append(patch_file)
            print(f"Applied patch: {patch_file}")
        else:
            print(f"Warning: Patch file not found: {src}")

    return applied


def build_drive_frontend():
    """Rebuild Drive frontend after applying patches."""
    drive_module_path = frappe.get_app_path("drive")
    drive_app_path = os.path.dirname(drive_module_path)
    frontend_dir = os.path.join(drive_app_path, "frontend")

    if not os.path.exists(frontend_dir):
        frappe.throw(f"Drive frontend directory not found: {frontend_dir}")

    print("Building Drive frontend...")

    # Check if pnpm is available
    try:
        result = subprocess.run(
            ["pnpm", "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            print(f"Build stderr: {result.stderr}")
            frappe.throw(f"Drive frontend build failed: {result.stderr}")

        print("Drive frontend built successfully")
        return True

    except FileNotFoundError:
        print("pnpm not found, trying npm...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            frappe.throw(f"Drive frontend build failed: {result.stderr}")

        print("Drive frontend built successfully")
        return True
    except subprocess.TimeoutExpired:
        frappe.throw("Drive frontend build timed out")


def apply_all(rebuild=True):
    """
    Apply all Drive patches and optionally rebuild frontend.

    Args:
        rebuild: If True, rebuild Drive frontend after applying patches
    """
    print("=" * 50)
    print("Applying Drive frontend patches")
    print("=" * 50)

    # Check if Drive app is installed
    try:
        frappe.get_app_path("drive")
    except Exception:
        print("Drive app not installed, skipping patches")
        return {"status": "skipped", "reason": "Drive app not installed"}

    # Apply Vue patches
    applied = apply_vue_patches()

    if not applied:
        print("No patches were applied")
        return {"status": "no_patches", "applied": []}

    # Rebuild frontend
    if rebuild:
        build_drive_frontend()

    print("=" * 50)
    print(f"Successfully applied {len(applied)} patches")
    print("=" * 50)

    return {"status": "success", "applied": applied}


def check_patches():
    """Check if patches are applied to Drive app."""
    patches_dir = get_patches_dir()
    drive_preview_dir = get_drive_frontend_dir()

    patches = ["MSOfficePreview.vue", "PDFPreview.vue"]
    status = {}

    for patch_file in patches:
        src = os.path.join(patches_dir, patch_file)
        dst = os.path.join(drive_preview_dir, patch_file)

        if not os.path.exists(src):
            status[patch_file] = "patch_missing"
        elif not os.path.exists(dst):
            status[patch_file] = "not_applied"
        else:
            # Compare file contents
            with open(src, "r") as f:
                src_content = f.read()
            with open(dst, "r") as f:
                dst_content = f.read()

            if src_content == dst_content:
                status[patch_file] = "applied"
            else:
                status[patch_file] = "outdated"

    return status
