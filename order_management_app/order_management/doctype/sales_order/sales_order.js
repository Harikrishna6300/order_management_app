// Copyright (c) 2026, Tridasa

frappe.ui.form.on("Sales Order", {

    refresh(frm) {

        // Show button only in Draft
        if (frm.doc.docstatus === 0 && frm.doc.status !== "Confirmed") {

            frm.add_custom_button("Mark Confirmed", () => {

                // Save document first
                frm.save().then(() => {

                    frappe.call({
                        method: "order_management_app.order_management.doctype.sales_order.sales_order.mark_confirmed",
                        args: {
                            docname: frm.doc.name
                        },
                        freeze: true,
                        freeze_message: "Confirming Order...",
                        callback: function (r) {

                            if (r.message) {
                                frm.reload_doc();
                                frappe.msgprint("Order Confirmed Successfully");
                            }
                        }
                    });

                });

            });
        }
    }
});
