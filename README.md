# Frappe Customizations

A Frappe app for maintaining framework customizations, patches, and fixtures across Frappe updates.

## Purpose

This app serves as the central location for all Frappe framework customizations:
- Custom Fields
- Property Setters
- Client Scripts
- Server Scripts
- Print Formats
- Doctype Overrides
- Patches for upstream app bugs

## Why Use a Customizations App?

Customizations made directly in the Frappe UI are stored in the database. While they survive container restarts and rebuilds (because the database is persisted), they can be:
- Lost if the database is reset
- Difficult to version control
- Hard to replicate across environments

By using fixtures, customizations are exported to JSON files that:
- Can be version controlled
- Are automatically applied on `bench migrate`
- Survive all updates and rebuilds

## Usage

### Exporting Customizations

After making customizations in the Frappe UI:

```bash
# From within the container
bench --site <sitename> export-fixtures --app frappe_customizations

# Or using the provided script
./scripts/export-fixtures.sh
```

### Adding Doctype Overrides

1. Create a new Python file in `frappe_customizations/overrides/`
2. Add the override mapping to `hooks.py`:
   ```python
   override_doctype_class = {
       "Sales Invoice": "frappe_customizations.overrides.sales_invoice.CustomSalesInvoice"
   }
   ```

### Adding Custom JS/CSS

1. Add files to `frappe_customizations/public/js/` or `frappe_customizations/public/css/`
2. Uncomment and modify in `hooks.py`:
   ```python
   app_include_css = "/assets/frappe_customizations/css/custom.css"
   app_include_js = "/assets/frappe_customizations/js/custom.js"
   ```

### Adding Patches

1. Create a patch file in `frappe_customizations/patches/`
2. Add the patch path to `patches.txt`:
   ```
   frappe_customizations.patches.your_patch_name
   ```

## Drive App Customizations

This app includes customizations for the Frappe Drive app:

### Document Preview Service

Replaces Microsoft's external preview service with local LibreOffice conversion for Office documents (DOCX, XLSX, PPTX, etc.).

**Requirements:**
- LibreOffice must be installed in the container/server
- Install with: `apt-get install -y libreoffice-writer libreoffice-calc libreoffice-impress --no-install-recommends`

**Features:**
- Converts Office documents to PDF using LibreOffice headless mode
- Caches converted PDFs for performance
- Automatic cleanup of old previews (weekly scheduled task)
- No external service dependencies

### Vue Component Patches

Patches for Drive frontend components to fix preview loading issues:
- `MSOfficePreview.vue` - LibreOffice-based document preview
- `PDFPreview.vue` - Fixed PDF preview re-rendering

**Applying Patches:**

After installing/updating the Drive app, apply the patches:

```bash
# Apply patches and rebuild frontend
bench execute frappe_customizations.drive_patches.apply_patches.apply_all

# Or apply patches only (without rebuilding)
bench execute frappe_customizations.drive_patches.apply_patches.apply_all --kwargs '{"rebuild": false}'

# Then manually rebuild
cd apps/drive/frontend && pnpm run build
```

**Check Patch Status:**

```bash
bench execute frappe_customizations.drive_patches.apply_patches.check_patches
```

## Organization

This app is part of the `frappe-accelerated` organization:
- **frappe_customizations** - Framework-level customizations and patches
- **frappe_{app_name}** - Domain-specific custom apps

## License

MIT
