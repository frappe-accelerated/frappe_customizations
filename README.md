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

## Organization

This app is part of the `frappe-accelerated` organization:
- **frappe_customizations** - Framework-level customizations and patches
- **frappe_{app_name}** - Domain-specific custom apps

## License

MIT
