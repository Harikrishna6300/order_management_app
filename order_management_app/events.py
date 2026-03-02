# events.py
import frappe

def sales_order_workflow_update(doc, method):
    """
    Handles workflow updates for Sales Order
    """
    if doc.workflow_state == "Confirmed":
        frappe.logger().info(f"Sales Order {doc.name} confirmed, enqueueing email")
        frappe.enqueue(
            "order_management_app.tasks.send_email",
            order_name=doc.name,
            queue="default",
            timeout=300
        )

    elif doc.workflow_state == "Cancelled":
        frappe.logger().info(f"Sales Order {doc.name} workflow cancelled")
        # Actually cancel the document to set docstatus=2
        if doc.docstatus != 2:
            # This triggers standard Frappe cancel logic
            doc.cancel()
            frappe.db.commit()  # Ensure changes are saved
            frappe.logger().info(f"Sales Order {doc.name} docstatus set to Cancelled")
