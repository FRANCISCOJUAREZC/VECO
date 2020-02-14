# -*- coding: utf-8 -*-
# © 2019 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_notes = fields.Char(copy=False)
