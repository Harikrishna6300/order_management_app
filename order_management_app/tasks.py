# order_management_app/tasks.py

import frappe

def send_email(order_name):
    """
    Sends confirmation email for the given Sales Order.
    Works in Frappe v15+
    """
    try:
        order = frappe.get_doc("Sales Order", order_name)

        # Get customer email from Customer Doctype
        customer_email = frappe.db.get_value(
            "Customer",
            order.customer,
            "email"
        )

        if not customer_email:
            frappe.log_error(
                message=f"No email found for customer {order.customer}",
                title="Email Not Sent"
            )
            return

        # Prepare email message
        message = f"""
        <p>Dear {order.customer_name or ''},</p>
        <p>Your order <strong>{order.name}</strong> has been confirmed on {order.transaction_date}.</p>
        <p>Total Amount: {order.grand_total}</p>
        <p>Thank you!</p>
        """

        # Send Email
        frappe.sendmail(
            recipients=[customer_email],
            subject=f"Order Confirmation - {order.name}",
            message=message,
            reference_doctype="Sales Order",
            reference_name=order.name
        )

        frappe.db.commit()

        frappe.log_error(
            message=f"Confirmation email sent to {customer_email} for {order.name}",
            title="Email Sent"
        )

    except Exception as e:
        frappe.log_error(message=str(e), title="Send Email Error")