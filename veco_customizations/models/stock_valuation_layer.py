# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    unit_cost = fields.Monetary(readonly=False)
    remaining_qty = fields.Monetary(readonly=False)

    @api.onchange('unit_cost')
    def _onchange_unit_cost(self):
        self.value = self.unit_cost * self.quantity
        self.remaining_value = self.unit_cost * self.remaining_qty

    @api.onchange('remaining_qty')
    def _onchange_remaining_qty(self):
        self.remaining_value = self.unit_cost * self.remaining_qty
