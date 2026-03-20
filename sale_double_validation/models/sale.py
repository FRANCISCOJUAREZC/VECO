# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(
        selection_add=[("to_approve", "To Approve")],
        ondelete={"to_approve": "set default"},
    )

    def is_amount_to_approve(self):
        self.ensure_one()
        company_currency = self.company_id.currency_id
        limit_amount = self.company_id.so_double_validation_amount

        limit_amount = company_currency._convert(
            limit_amount,
            self.currency_id,
            self.company_id,
            self.date_order or fields.Date.today(),
        )

        return (
            float_compare(
                limit_amount,
                self.amount_total,
                precision_rounding=self.currency_id.rounding,
            ) <= 0
        )

    def is_to_approve(self):
        self.ensure_one()
        return (
            self.company_id.so_double_validation == "two_step"
            and self.is_amount_to_approve()
            and not self.env.user.has_group("sales_team.group_sale_manager")
        )

    @api.model
    def create(self, vals):
        obj = super().create(vals)
        if obj.is_to_approve():
            obj.state = "to_approve"
        return obj

    def action_approve(self):
        self.write({"state": "draft"})
