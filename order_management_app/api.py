# order_management_app/api.py
import frappe


# =========================================================
# Get Confirmed Orders API
# =========================================================
@frappe.whitelist()
def get_orders():
    """
    Returns all confirmed Sales Orders with customer and items.
    Sends confirmation email asynchronously if not sent yet.
    """
    try:
        response_data = []

        # Fetch all confirmed orders
        orders = frappe.get_all(
            "Sales Order",
            filters={"status": "Confirmed"},
            fields=[
                "name",
                "customer",
                "order_date",
                "total_amount",
                "email_sent_on_confirmed",
            ],
        )

        for order in orders:
            # Fetch customer details
            customer = frappe.get_all(
                "Customer",
                filters={"name": order.customer},
                fields=["customer_name", "email_id"],
            )

            # Fetch order items
            items = frappe.get_all(
                "Sales Order Item",
                filters={"parent": order.name},
                fields=["item_code", "item_name", "qty", "rate", "amount"],
            )

            # Enqueue email if not sent
            if not order.email_sent_on_confirmed:
                frappe.enqueue(
                    "order_management_app.tasks.send_email",
                    queue="default",
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
                    "order_date": order.order_date,
                    "total_amount": order.total_amount,
                    "customer": customer[0] if customer else {},
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
# Cached Item List API  ✅ (Caching Requirement)
# =========================================================
@frappe.whitelist()
def get_cached_items():
    """
    Cache frequently accessed Item list using frappe.cache().
    First call -> Database
    Next calls -> Cache (Redis)
    """
    try:
        cache_key = "order_management_item_list"

        # 1️⃣ Check cache
        cached_items = frappe.cache().get_value(cache_key)

        if cached_items:
            return {
                "status": "success",
                "source": "cache",
                "data": cached_items,
            }

        # 2️⃣ Fetch from DB
        items = frappe.get_all(
            "Item",
            fields=["name", "item_name", "price", "stock_quantity"],
        )

        # 3️⃣ Store in cache (5 min expiry)
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
# Hook function for Sales Order update
# =========================================================
def sales_order_update(doc, method):
    """
    Triggered by doc_events on Sales Order update.
    Sends confirmation email if status becomes 'Confirmed'.
    """

    if doc.status == "Confirmed" and not doc.email_sent_on_confirmed:

        frappe.enqueue(
            "order_management_app.tasks.send_email",
            queue="default",
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
