"""
Setup hooks for frappe_customizations app.

These functions run during app installation and migration.
"""
import frappe


def after_install():
    """Run after frappe_customizations is installed."""
    print("Running frappe_customizations after_install...")
    apply_drive_patches_if_installed()


def after_migrate():
    """Run after bench migrate."""
    print("Running frappe_customizations after_migrate...")
    apply_drive_patches_if_installed()


def apply_drive_patches_if_installed():
    """Apply Drive patches if Drive app is installed."""
    try:
        # Check if Drive is installed
        frappe.get_app_path("drive")
    except Exception:
        print("Drive app not installed, skipping frontend patches")
        return

    try:
        from frappe_customizations.drive_patches.apply_patches import apply_all
        # Don't rebuild automatically during migrate - it can be slow
        # User should run: bench execute frappe_customizations.drive_patches.apply_patches.apply_all
        result = apply_all(rebuild=False)
        if result.get("status") == "success":
            print(f"Applied Drive patches: {result.get('applied')}")
            print("NOTE: Run 'cd apps/drive/frontend && pnpm run build' to rebuild Drive frontend")
    except Exception as e:
        print(f"Warning: Could not apply Drive patches: {e}")
