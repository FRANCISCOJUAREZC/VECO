# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_protected_fields(self):
        """ Overridden to avoid error messages when the sale order is locked. """
        return []
