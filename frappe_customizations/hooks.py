app_name = "frappe_customizations"
app_title = "Frappe Customizations"
app_publisher = "Frappe Accelerated"
app_description = "Frappe framework customizations, patches, and fixtures"
app_email = "admin@frappe-accelerated.com"
app_license = "MIT"

# Required apps
required_apps = ["frappe"]

# Fixtures - auto-imported on bench migrate
# These customizations will survive updates and rebuilds
fixtures = [
    # Custom Fields created in this app's module
    {"doctype": "Custom Field", "filters": [["module", "=", "Frappe Customizations"]]},
    # Property Setters for modifying existing field properties
    {"doctype": "Property Setter", "filters": [["module", "=", "Frappe Customizations"]]},
    # Client Scripts for frontend customizations
    {"doctype": "Client Script", "filters": [["module", "=", "Frappe Customizations"]]},
    # Server Scripts for backend customizations
    {"doctype": "Server Script", "filters": [["module", "=", "Frappe Customizations"]]},
    # Custom Print Formats
    {"doctype": "Print Format", "filters": [["module", "=", "Frappe Customizations"]]},
    # Custom Reports
    {"doctype": "Report", "filters": [["module", "=", "Frappe Customizations"]]},
    # Workspace customizations
    {"doctype": "Workspace", "filters": [["module", "=", "Frappe Customizations"]]},
]

# Override standard doctype classes
# Uncomment and modify as needed
# override_doctype_class = {
#     "Sales Invoice": "frappe_customizations.overrides.sales_invoice.CustomSalesInvoice",
#     "Customer": "frappe_customizations.overrides.customer.CustomCustomer",
# }

# Document Events
# Hook on document methods and events
# doc_events = {
#     "Sales Invoice": {
#         "on_submit": "frappe_customizations.overrides.sales_invoice.on_submit",
#         "on_cancel": "frappe_customizations.overrides.sales_invoice.on_cancel",
#     }
# }

# Scheduled Tasks
# scheduler_events = {
#     "daily": [
#         "frappe_customizations.tasks.daily"
#     ],
#     "hourly": [
#         "frappe_customizations.tasks.hourly"
#     ],
# }

# Jinja template customizations
# jinja = {
#     "methods": [
#         "frappe_customizations.utils.jinja_methods"
#     ],
# }

# Website user home page (for portal users)
# website_context = {
#     "my_items": "frappe_customizations.utils.get_my_items"
# }

# Include custom CSS and JS in desk
app_include_css = "/assets/frappe_customizations/css/custom.css"
# app_include_js = "/assets/frappe_customizations/js/frappe_customizations.js"

# Include custom JS in website
# web_include_js = "/assets/frappe_customizations/js/frappe_customizations_web.js"

# Include custom CSS in website
# web_include_css = "/assets/frappe_customizations/css/frappe_customizations_web.css"
