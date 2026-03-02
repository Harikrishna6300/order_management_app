import frappe
from frappe.model.document import Document
from frappe import _


class SalesOrder(Document):

    # --------------------------------------------------
    # BEFORE SAVE → Draft Status
    # --------------------------------------------------
    def before_save(self):
        if self.docstatus == 0:
            self.status = "Draft"

            frappe.logger().info(
                f"Sales Order {self.name} saved as Draft"
            )

    # --------------------------------------------------
    # VALIDATION LOGIC
    # --------------------------------------------------
    def validate(self):

        frappe.logger().info(
            f"Validating Sales Order {self.name}"
        )

        # Order must contain at least one item
        if not self.items:
            frappe.throw(_("Sales Order must contain at least one item."))

        total_amount = 0

        # Loop through child table
        for row in self.items:

            # Fetch item document
            item_doc = frappe.get_doc("Item", row.item)
            available_stock = item_doc.stock_quantity

            # Quantity validation
            if row.quantity <= 0:
                frappe.logger().error(
                    f"Invalid quantity for item {row.item} in {self.name}"
                )
                frappe.throw(
                    _(f"Quantity must be greater than 0 for Item {row.item}")
                )

            # Stock validation
            if row.quantity > available_stock:
                frappe.logger().warning(
                    f"Stock shortage for {row.item}. "
                    f"Requested: {row.quantity}, Available: {available_stock}"
                )
                frappe.throw(
                    _(f"Insufficient stock for Item {row.item}. "
                      f"Available stock: {available_stock}")
                )

            # Auto calculate row amount
            row.amount = row.quantity * row.rate
            total_amount += row.amount

        # Set total automatically
        self.total_amount = total_amount

        frappe.logger().info(
            f"Validation completed for {self.name}. Total Amount: {self.total_amount}"
        )

    # --------------------------------------------------
    # ON SUBMIT → Reduce Stock
    # --------------------------------------------------
    def on_submit(self):

        frappe.logger().info(
            f"Submitting Sales Order {self.name}"
        )

        for row in self.items:

            item_doc = frappe.get_doc("Item", row.item)

            item_doc.stock_quantity = (
                item_doc.stock_quantity - row.quantity
            )

            item_doc.save()

            frappe.logger().info(
                f"Stock reduced for Item {row.item} by {row.quantity}. "
                f"New stock: {item_doc.stock_quantity}"
            )

        self.status = "Confirmed"

        frappe.logger().info(
            f"Order confirmed: {self.name}"
        )

    # --------------------------------------------------
    # ON CANCEL → Restore Stock
    # --------------------------------------------------
    def on_cancel(self):

        frappe.logger().info(
            f"Cancelling Sales Order {self.name}"
        )

        for row in self.items:

            item_doc = frappe.get_doc("Item", row.item)

            item_doc.stock_quantity = (
                item_doc.stock_quantity + row.quantity
            )

            item_doc.save()

            frappe.logger().info(
                f"Stock restored for Item {row.item} by {row.quantity}. "
                f"New stock: {item_doc.stock_quantity}"
            )

        self.status = "Cancelled"

        frappe.logger().info(
            f"Order cancelled: {self.name}"
        )


# ======================================================
# CUSTOM BUTTON BACKEND METHOD
# ======================================================

@frappe.whitelist()
def mark_confirmed(docname):
    """
    Called from custom button using frappe.call
    """

    frappe.logger().info(
        f"Manual confirmation requested for Sales Order {docname}"
    )

    # Fetch document
    doc = frappe.get_doc("Sales Order", docname)

    # Allow only Draft documents
    if doc.docstatus != 0:
        frappe.logger().warning(
            f"Attempt to confirm non-draft order {docname}"
        )
        frappe.throw(_("Only Draft orders can be marked as Confirmed"))

    # Update status
    doc.status = "Confirmed"

    # Save document
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    frappe.logger().info(
        f"Sales Order {docname} manually marked as Confirmed"
    )

    return True
