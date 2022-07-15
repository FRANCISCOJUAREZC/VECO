# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_protected_fields(self):
        """ Method Overriden in order to avoid a error msg when the sale order is locked"""
        return []

    def _finalize_invoices(self, invoices, references):
        """
        Invoked after creating invoices at the end of action_invoice_create.
        :param invoices: {group_key: invoice}
        :param references: {invoice: order}
        """
        for invoice in invoices.values():
            for line in invoice.invoice_line_ids:
                if line.sale_line_ids:
                    line.name = line.sale_line_ids[0].name
        return super(SaleOrder, self)._finalize_invoices(invoices, references)
