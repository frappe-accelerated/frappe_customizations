import frappe


def execute():
    """Fix invalid filter format in Education workspace shortcut.

    The Education app has a shortcut with an invalid 5-element filter:
    ["Sales Invoice", "fee_schedule", "is", "set", false]

    This patch corrects it to the valid 4-element format:
    ["Sales Invoice", "fee_schedule", "is", "not set"]
    """
    shortcuts = frappe.get_all(
        "Workspace Shortcut",
        filters={"link_to": "Sales Invoice"},
        fields=["name", "stats_filter"],
    )

    for shortcut in shortcuts:
        if shortcut.stats_filter and "is" in shortcut.stats_filter and '"set"' in shortcut.stats_filter:
            new_filter = '[["Sales Invoice", "fee_schedule", "is", "not set"]]'
            frappe.db.set_value("Workspace Shortcut", shortcut.name, "stats_filter", new_filter)

    frappe.db.commit()
