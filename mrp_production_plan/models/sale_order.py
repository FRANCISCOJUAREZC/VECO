# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    plant_commitment_date = fields.Datetime(
        tracking=True,
    )
