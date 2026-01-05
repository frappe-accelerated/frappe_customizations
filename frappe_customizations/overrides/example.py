"""
Example doctype override.

To use this, add to hooks.py:
    override_doctype_class = {
        "Sales Invoice": "frappe_customizations.overrides.example.CustomSalesInvoice"
    }
"""
import frappe
from frappe import _


class CustomSalesInvoice:
    """
    Example override for Sales Invoice.
    Inherits all methods from the original doctype.
    """

    def validate(self):
        # Call the original validate method first
        super().validate()

        # Add your custom validation logic here
        # Example: self.validate_custom_field()

    def before_save(self):
        super().before_save()
        # Add custom logic before saving

    def after_insert(self):
        super().after_insert()
        # Add custom logic after insert
