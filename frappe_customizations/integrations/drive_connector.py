"""
Drive Connector for Frappe Insights

This module provides the connection layer between Frappe Drive and Frappe Insights,
allowing CSV/Excel files stored in Drive to be queried through Insights.
"""

import frappe
import pandas as pd
import io
from pathlib import Path
from typing import Optional


class DriveConnector:
    """
    Connector class that handles Drive file operations for Insights.

    Files are cached locally as Parquet format for efficient querying
    via DuckDB/Ibis.
    """

    # Supported MIME types for data files
    SUPPORTED_MIME_TYPES = [
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]

    def __init__(self, data_source: Optional[str] = None):
        """
        Initialize the Drive connector.

        Args:
            data_source: Name of the Insights Data Source document (optional)
        """
        self.data_source = data_source
        self.cache_dir = Path(frappe.get_site_path("private", "files", "drive_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "drive_insights.duckdb"

    def list_files(self, folder_id: Optional[str] = None) -> list:
        """
        List CSV/Excel files accessible to current user.

        Args:
            folder_id: Optional folder ID to filter files

        Returns:
            List of file metadata dictionaries
        """
        filters = {
            "is_active": 1,
            "is_group": 0,
            "mime_type": ["in", self.SUPPORTED_MIME_TYPES],
        }

        if folder_id:
            filters["parent_entity"] = folder_id

        files = frappe.get_list(
            "Drive File",
            filters=filters,
            fields=["name", "title", "mime_type", "file_size", "modified", "owner"],
            order_by="modified desc",
        )

        # Add human-readable file size
        for f in files:
            f["file_size_formatted"] = self._format_file_size(f.get("file_size", 0))
            f["is_cached"] = self._is_cached(f["name"])

        return files

    def list_folders(self, parent_id: Optional[str] = None) -> list:
        """
        List folders accessible to current user.

        Args:
            parent_id: Optional parent folder ID

        Returns:
            List of folder metadata dictionaries
        """
        filters = {
            "is_active": 1,
            "is_group": 1,
        }

        if parent_id:
            filters["parent_entity"] = parent_id
        else:
            filters["parent_entity"] = ["is", "not set"]

        return frappe.get_list(
            "Drive File",
            filters=filters,
            fields=["name", "title", "modified", "owner"],
            order_by="title asc",
        )

    def get_file_content(self, file_id: str) -> bytes:
        """
        Get raw file content from Drive.

        Args:
            file_id: Drive file ID

        Returns:
            File content as bytes
        """
        # Import Drive's file content function
        from drive.api.files import get_file_content as drive_get_content

        return drive_get_content(file_id)

    def import_file(self, file_id: str) -> dict:
        """
        Import a Drive file to local Parquet cache.

        Args:
            file_id: Drive file ID to import

        Returns:
            Dictionary with import results (table_name, columns, row_count, etc.)
        """
        # Get file metadata
        file_doc = frappe.get_doc("Drive File", file_id)

        # Check permission
        if not self._user_has_permission(file_id, "read"):
            frappe.throw("You do not have permission to access this file")

        # Get file content
        content = self.get_file_content(file_id)

        # Parse based on MIME type
        df = self._parse_file_content(content, file_doc.mime_type, file_doc.title)

        # Clean column names (remove special chars, spaces)
        df.columns = [self._clean_column_name(col) for col in df.columns]

        # Save as Parquet
        parquet_path = self.cache_dir / f"{file_id}.parquet"
        df.to_parquet(parquet_path, index=False)

        # Register in DuckDB
        self._register_parquet_in_duckdb(file_id, file_doc.title, parquet_path)

        return {
            "file_id": file_id,
            "table_name": self._sanitize_table_name(file_doc.title),
            "original_name": file_doc.title,
            "columns": [
                {"name": col, "type": str(dtype)}
                for col, dtype in zip(df.columns, df.dtypes)
            ],
            "row_count": len(df),
            "parquet_path": str(parquet_path),
            "cached_at": frappe.utils.now(),
        }

    def sync_file(self, file_id: str) -> dict:
        """
        Re-sync a previously imported file (refresh data from Drive).

        Args:
            file_id: Drive file ID to sync

        Returns:
            Dictionary with sync results
        """
        return self.import_file(file_id)

    def remove_file(self, file_id: str) -> bool:
        """
        Remove a file from the cache.

        Args:
            file_id: Drive file ID to remove

        Returns:
            True if successful
        """
        parquet_path = self.cache_dir / f"{file_id}.parquet"

        if parquet_path.exists():
            parquet_path.unlink()

        # Remove from DuckDB registry
        self._unregister_from_duckdb(file_id)

        return True

    def get_table_schema(self, file_id: str) -> list:
        """
        Get the schema (columns and types) for a cached file.

        Args:
            file_id: Drive file ID

        Returns:
            List of column dictionaries with name and type
        """
        parquet_path = self.cache_dir / f"{file_id}.parquet"

        if not parquet_path.exists():
            frappe.throw(f"File {file_id} not found in cache. Please import it first.")

        df = pd.read_parquet(parquet_path)

        return [
            {"name": col, "type": str(dtype)}
            for col, dtype in zip(df.columns, df.dtypes)
        ]

    def get_table_preview(self, file_id: str, limit: int = 100) -> list:
        """
        Get a preview of the data in a cached file.

        Args:
            file_id: Drive file ID
            limit: Maximum number of rows to return

        Returns:
            List of row dictionaries
        """
        parquet_path = self.cache_dir / f"{file_id}.parquet"

        if not parquet_path.exists():
            frappe.throw(f"File {file_id} not found in cache. Please import it first.")

        df = pd.read_parquet(parquet_path).head(limit)

        return df.to_dict(orient="records")

    def get_ibis_connection(self):
        """
        Return a DuckDB Ibis connection for querying cached files.

        Returns:
            Ibis DuckDB connection
        """
        try:
            import ibis

            return ibis.duckdb.connect(str(self.db_path), read_only=False)
        except ImportError:
            frappe.throw("ibis-framework is required. Install with: pip install ibis-framework[duckdb]")

    def test_connection(self) -> dict:
        """
        Test the Drive connection.

        Returns:
            Dictionary with connection status
        """
        try:
            # Try to list files - this tests Drive access
            files = self.list_files()

            return {
                "status": "success",
                "message": f"Connected. Found {len(files)} accessible data files.",
                "file_count": len(files),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    # Private helper methods

    def _parse_file_content(self, content: bytes, mime_type: str, filename: str) -> pd.DataFrame:
        """Parse file content based on MIME type."""
        if "csv" in mime_type.lower() or filename.lower().endswith(".csv"):
            # Try different encodings
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    return pd.read_csv(io.StringIO(content.decode(encoding)))
                except UnicodeDecodeError:
                    continue
            frappe.throw("Could not decode CSV file. Please ensure it's UTF-8 encoded.")

        elif "spreadsheet" in mime_type.lower() or filename.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(content))

        else:
            frappe.throw(f"Unsupported file type: {mime_type}")

    def _clean_column_name(self, name: str) -> str:
        """Clean column name for SQL compatibility."""
        import re

        # Replace spaces and special chars with underscore
        cleaned = re.sub(r"[^\w]", "_", str(name))
        # Remove leading numbers
        if cleaned and cleaned[0].isdigit():
            cleaned = "_" + cleaned
        # Lowercase
        return cleaned.lower()

    def _sanitize_table_name(self, name: str) -> str:
        """Sanitize filename for use as table name."""
        import re

        # Remove extension
        name = Path(name).stem
        # Replace special chars
        sanitized = re.sub(r"[^\w]", "_", name)
        # Lowercase
        return sanitized.lower()

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _is_cached(self, file_id: str) -> bool:
        """Check if a file is already cached."""
        parquet_path = self.cache_dir / f"{file_id}.parquet"
        return parquet_path.exists()

    def _user_has_permission(self, file_id: str, permission: str = "read") -> bool:
        """Check if current user has permission to access file."""
        try:
            # Use Drive's permission check
            from drive.utils.files import user_has_permission

            return user_has_permission(file_id, permission)
        except ImportError:
            # Fallback: check if user can access via get_list
            return frappe.db.exists("Drive File", file_id)

    def _register_parquet_in_duckdb(self, file_id: str, title: str, parquet_path: Path):
        """Register a Parquet file as a view in DuckDB."""
        try:
            import duckdb

            table_name = self._sanitize_table_name(title)

            conn = duckdb.connect(str(self.db_path))
            conn.execute(f"""
                CREATE OR REPLACE VIEW "{table_name}" AS
                SELECT * FROM read_parquet('{parquet_path}')
            """)
            conn.close()
        except Exception as e:
            frappe.log_error(f"Failed to register in DuckDB: {e}", "Drive Connector")

    def _unregister_from_duckdb(self, file_id: str):
        """Remove a view from DuckDB."""
        try:
            import duckdb
            # We'd need to track table_name -> file_id mapping
            # For now, skip this cleanup
            pass
        except Exception:
            pass
