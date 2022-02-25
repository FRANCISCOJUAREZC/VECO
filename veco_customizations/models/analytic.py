# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _sale_determine_order_line(self):
        """ Automatically set the SO line on the analytic line,
            for the expense/vendor bills flow. It retrives
            an existing line, or create a new one (upselling expenses).
        """
        # determine SO : first SO open linked to AA
        sale_order_map = self._sale_determine_order()
        # determine so line
        value_to_write = {}
        for analytic_line in self:
            sale_order = sale_order_map.get(analytic_line.id)
            if not sale_order:
                continue

            if sale_order.state not in ['sale', 'done']:
                message_unconfirmed = _(
                    'The Sales Order %s linked to the Analytic Account %s '
                    'must be validated before registering expenses.')
                messages = {
                    'draft': message_unconfirmed,
                    'sent': message_unconfirmed,
                    'cancel': _(
                        'The Sales Order %s linked to the Analytic Account %s '
                        'is cancelled. You cannot register an expense on a '
                        'cancelled Sales Order.'),
                }
                raise UserError(messages[sale_order.state] % (
                    sale_order.name, analytic_line.account_id.name))

            so_line = None
            price = analytic_line._sale_get_invoice_price(sale_order)
            if (analytic_line.product_id.expense_policy == 'sales_price' and
                    analytic_line.product_id.invoice_policy == 'delivery'):
                so_line = self.env['sale.order.line'].search([
                    ('order_id', '=', sale_order.id),
                    ('price_unit', '=', price),
                    ('product_id', '=', self.product_id.id),
                    ('is_expense', '=', True),
                ], limit=1)

            if not so_line:
                # generate a new SO line
                so_line_values = (
                    analytic_line._sale_prepare_sale_order_line_values(
                        sale_order, price))
                so_line = self.env['sale.order.line'].create(so_line_values)
                so_line._compute_tax_id()
            # if so line found or created, then update AAL (this will trigger
            # the recomputation of qty delivered on SO line)
            if so_line:
                value_to_write.setdefault(
                    so_line.id, self.env['account.analytic.line'])
                value_to_write[so_line.id] |= analytic_line

        # write so line on (maybe) multiple AAL to trigger only one
        # read_group per SO line
        for so_line_id, analytic_lines in value_to_write.items():
            if analytic_lines:
                analytic_lines.write({'so_line': so_line_id})
