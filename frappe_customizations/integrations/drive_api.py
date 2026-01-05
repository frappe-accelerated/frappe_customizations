"""
API endpoints for Insights Drive Connector

These whitelisted methods provide the interface between the Insights UI
and the Drive connector backend.
"""

import frappe
from frappe import _
from .drive_connector import DriveConnector


@frappe.whitelist()
def list_drive_files(folder_id: str = None) -> list:
    """
    List available Drive files for import.

    Args:
        folder_id: Optional folder ID to filter files

    Returns:
        List of file metadata
    """
    connector = DriveConnector()
    return connector.list_files(folder_id)


@frappe.whitelist()
def list_drive_folders(parent_id: str = None) -> list:
    """
    List Drive folders for navigation.

    Args:
        parent_id: Optional parent folder ID

    Returns:
        List of folder metadata
    """
    connector = DriveConnector()
    return connector.list_folders(parent_id)


@frappe.whitelist()
def import_drive_file(file_id: str, data_source: str = None) -> dict:
    """
    Import a Drive file as a table in Insights.

    Args:
        file_id: Drive file ID to import
        data_source: Optional Insights Data Source name

    Returns:
        Import results with table info
    """
    connector = DriveConnector(data_source)
    result = connector.import_file(file_id)

    # Log the import
    frappe.logger().info(f"Imported Drive file {file_id} as table {result['table_name']}")

    return result


@frappe.whitelist()
def sync_drive_file(file_id: str, data_source: str = None) -> dict:
    """
    Re-sync a Drive file (refresh data from Drive).

    Args:
        file_id: Drive file ID to sync
        data_source: Optional Insights Data Source name

    Returns:
        Sync results
    """
    connector = DriveConnector(data_source)
    result = connector.sync_file(file_id)

    frappe.msgprint(_("File synced successfully. {0} rows imported.").format(result["row_count"]))

    return result


@frappe.whitelist()
def remove_drive_file(file_id: str) -> dict:
    """
    Remove a Drive file from the Insights cache.

    Args:
        file_id: Drive file ID to remove

    Returns:
        Status message
    """
    connector = DriveConnector()
    success = connector.remove_file(file_id)

    return {
        "success": success,
        "message": _("File removed from cache") if success else _("Failed to remove file"),
    }


@frappe.whitelist()
def get_file_schema(file_id: str) -> list:
    """
    Get the schema (columns) for a cached Drive file.

    Args:
        file_id: Drive file ID

    Returns:
        List of column definitions
    """
    connector = DriveConnector()
    return connector.get_table_schema(file_id)


@frappe.whitelist()
def get_file_preview(file_id: str, limit: int = 100) -> list:
    """
    Get a preview of data from a cached Drive file.

    Args:
        file_id: Drive file ID
        limit: Maximum rows to return

    Returns:
        List of row data
    """
    connector = DriveConnector()
    return connector.get_table_preview(file_id, int(limit))


@frappe.whitelist()
def test_drive_connection() -> dict:
    """
    Test the Drive connection.

    Returns:
        Connection status
    """
    connector = DriveConnector()
    return connector.test_connection()


@frappe.whitelist()
def get_cached_files() -> list:
    """
    Get list of files currently in the Insights cache.

    Returns:
        List of cached file info
    """
    connector = DriveConnector()
    files = connector.list_files()

    # Filter to only cached files
    return [f for f in files if f.get("is_cached")]


@frappe.whitelist()
def browse_drive(folder_id: str = None) -> dict:
    """
    Browse Drive files and folders.

    Args:
        folder_id: Current folder ID (None for root)

    Returns:
        Dictionary with folders and files
    """
    connector = DriveConnector()

    return {
        "folders": connector.list_folders(folder_id),
        "files": connector.list_files(folder_id),
        "current_folder": folder_id,
    }
