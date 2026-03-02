import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum
from frappe.query_builder import Order

def execute(filters=None):
    # Ensure filters is always a dict
    if not isinstance(filters, dict):
        import json
        try:
            filters = json.loads(filters)
        except Exception:
            filters = {}

    so = DocType("Sales Order")
    c = DocType("Customer")

    total_sales_expr = Sum(so.total_amount).as_("total_sales")

    query = (
        frappe.qb.from_(so)
        .left_join(c).on(c.name == so.customer)
        .select(
            so.customer,
            c.customer_name,
            total_sales_expr
        )
        .where(so.docstatus == 1)
    )

    # Apply date filters
    if filters.get("from_date"):
        query = query.where(so.creation >= filters.get("from_date"))
    if filters.get("to_date"):
        query = query.where(so.creation <= filters.get("to_date"))

    query = query.groupby(so.customer, c.customer_name)
    query = query.orderby(total_sales_expr, order=Order.desc)

    result = query.run(as_dict=True)

    # Always return a list to prevent KeyError:0
    if result is None:
        return []

    return result
