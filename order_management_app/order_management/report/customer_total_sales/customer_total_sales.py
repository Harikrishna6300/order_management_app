import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum
from frappe.query_builder import Order


def execute(filters=None):
    filters = filters or {}

    # -----------------------------
    # Report Columns
    # -----------------------------
    columns = [
        {
            "label": "Customer",
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "label": "Total Sales",
            "fieldname": "total_sales",
            "fieldtype": "Currency",
            "width": 150
        }
    ]

    # -----------------------------
    # DocType Reference
    # -----------------------------
    so = DocType("Sales Order")

    # -----------------------------
    # Aggregate Function
    # -----------------------------
    total_sales = Sum(so.total_amount).as_("total_sales")

    # -----------------------------
    # Query Builder
    # -----------------------------
    query = (
        frappe.qb.from_(so)
        .select(
            so.customer,
            total_sales
        )
        .where(so.docstatus == 1)
        .groupby(so.customer)
        .orderby(total_sales, order=Order.desc)
    )

    # -----------------------------
    # Execute Query
    # -----------------------------
    data = query.run(as_dict=True)

    return columns, data