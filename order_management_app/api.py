# order_management_app/api.py

import frappe


# =========================================================
# Get Confirmed Orders API
# =========================================================
@frappe.whitelist()
def get_orders():
    """
    Returns confirmed Sales Orders with customer and items.
    Sends confirmation email asynchronously if not already sent.
    """
    try:
        response_data = []

        # Fetch submitted sales orders
        orders = frappe.get_all(
            "Sales Order",
            filters={"docstatus": 1},
            fields=[
                "name",
                "customer",
                "customer_name",
                "transaction_date",
                "grand_total",
                "email_sent_on_confirmed",
            ],
        )

        for order in orders:

            # Fetch customer email
            customer = frappe.get_value(
                "Customer",
                order.customer,
                ["customer_name", "email_id"],
                as_dict=True,
            )

            # Fetch order items
            items = frappe.get_all(
                "Sales Order Item",
                filters={"parent": order.name},
                fields=["item_code", "item_name", "qty", "rate", "amount"],
            )

            # Send email if not sent
            if not order.email_sent_on_confirmed:
                frappe.enqueue(
                    "order_management_app.tasks.send_email",
                    queue="short",
                    timeout=300,
                    order_name=order.name,
                )

                frappe.db.set_value(
                    "Sales Order",
                    order.name,
                    "email_sent_on_confirmed",
                    1,
                )

            response_data.append(
                {
                    "order_id": order.name,
                    "order_date": order.transaction_date,
                    "total_amount": order.grand_total,
                    "customer": customer or {},
                    "items": items,
                }
            )

        return {
            "status": "success",
            "count": len(response_data),
            "data": response_data,
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Orders API Error")
        return {"status": "error", "message": str(e)}


# =========================================================
# Cached Item List API
# =========================================================
@frappe.whitelist()
def get_cached_items():
    """
    Returns item list using Redis cache.
    First call -> Database
    Next calls -> Cache
    """

    try:

        cache_key = "order_management_item_list"

        # Check cache
        cached_items = frappe.cache().get_value(cache_key)

        if cached_items:
            return {
                "status": "success",
                "source": "cache",
                "data": cached_items,
            }

        # Fetch from database
        items = frappe.get_all(
            "Item",
            fields=["name", "item_name", "stock_uom"],
        )

        # Store in cache for 5 minutes
        frappe.cache().set_value(
            cache_key,
            items,
            expires_in_sec=300,
        )

        return {
            "status": "success",
            "source": "database",
            "data": items,
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Cached Item API Error")
        return {"status": "error", "message": str(e)}


# =========================================================
# Hook Function - Sales Order Confirmed
# =========================================================
def sales_order_update(doc, method):
    """
    Triggered when Sales Order is submitted.
    Sends confirmation email to customer.
    """

    try:

        # Check if email already sent
        if doc.email_sent_on_confirmed:
            return

        # Get customer email
        customer_email = frappe.db.get_value(
            "Customer",
            doc.customer,
            "email_id"
        )

        if not customer_email:
            return

        # Send email in background
        frappe.enqueue(
            "order_management_app.tasks.send_email",
            queue="short",
            timeout=300,
            order_name=doc.name,
        )

        # Mark email as sent
        frappe.db.set_value(
            "Sales Order",
            doc.name,
            "email_sent_on_confirmed",
            1,
        )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Sales Order Email Error"
        )