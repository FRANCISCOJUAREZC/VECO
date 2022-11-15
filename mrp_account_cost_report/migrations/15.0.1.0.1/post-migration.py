# -*- coding: utf-8 -*-
# Copyright 2022 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['mrp.production'].search([
        ('state', '=', 'done'),
    ])
    orders._compute_costs()
    orders._compute_sale_amount()
