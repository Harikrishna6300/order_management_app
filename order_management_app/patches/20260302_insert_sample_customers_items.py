import frappe
from frappe.utils import today

def execute():
    insert_sample_customers()
    insert_sample_items()

def insert_sample_customers():
    sample_customers = [
        {"customer_name": "ABC Traders", "email": "abc@traders.com", "phone": "9998887770", "status": "Active"},
        {"customer_name": "XYZ Enterprises", "email": "xyz@enterprises.com", "phone": "8887776660", "status": "Active"},
        {"customer_name": "John Doe", "email": "john@example.com", "phone": "7776665550", "status": "Inactive"}
    ]
    
    for cust in sample_customers:
        if not frappe.db.exists("Customer", cust["customer_name"]):
            frappe.get_doc({
                "doctype": "Customer",
                **cust
            }).insert(ignore_permissions=True)
            print(f"Inserted Customer: {cust['customer_name']}")
        else:
            print(f"Customer already exists: {cust['customer_name']}")

def insert_sample_items():
    sample_items = [
        {"item_name": "Laptop", "price": 50000, "stock_quantity": 10},
        {"item_name": "Mouse", "price": 500, "stock_quantity": 50},
        {"item_name": "Keyboard", "price": 1500, "stock_quantity": 30}
    ]
    
    for item in sample_items:
        if not frappe.db.exists("Item", item["item_name"]):
            frappe.get_doc({
                "doctype": "Item",
                **item
            }).insert(ignore_permissions=True)
            print(f"Inserted Item: {item['item_name']}")
        else:
            print(f"Item already exists: {item['item_name']}")
