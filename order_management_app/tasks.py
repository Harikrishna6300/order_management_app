# order_management_app/tasks.py
import frappe

def send_email(order_name):
    """
    Sends confirmation email for the given Sales Order.
    Works in Frappe v15+
    """
    try:
        order = frappe.get_doc("Sales Order", order_name)
        recipient = order.customer_email or order.contact_email

        if not recipient:
            frappe.log_error(message=f"No recipient email found for {order.name}", title="Email Not Sent")
            return

        # Prepare message
        message = f"""
        <p>Dear {order.customer_name or ''},</p>
        <p>Your order <strong>{order.name}</strong> has been confirmed on {order.order_date}.</p>
        <p>Total Amount: {order.total_amount}</p>
        <p>Thank you!</p>
        """

        # Send email using Frappe v15 API
        frappe.sendmail(
            recipients=[recipient],
            subject=f"Order Confirmation - {order.name}",
            message=message,
            reference_doctype="Sales Order",
            reference_name=order.name
        )

        frappe.db.commit()
        frappe.log_error(message=f"Confirmation email sent to {recipient} for {order.name}", title="Email Sent")

    except Exception as e:
        frappe.log_error(message=str(e), title="Send Email Error")
