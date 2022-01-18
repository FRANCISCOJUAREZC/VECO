# -*- coding: utf-8 -*-
# Copyright 2022 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    items = env['mrp.production.plan.item'].search(
        [('status', '=', "b. Entregado a Almacén"),
         ('completed', '=', False)])
    for item in items:
        mrp = item.mrp_id
        dest_location = mrp.location_dest_id
        sale_line = item.sale_line_id
        sfp_picks = (
            mrp.picking_ids.filtered(
                lambda x: x.location_id == dest_location
                and x.state == 'done')
            or sale_line.order_id.picking_ids.filtered(
                lambda x: x.location_id == dest_location
                and x.state == 'done')
        )
        for sfp_pick in sfp_picks:
            if mrp.product_id in sfp_pick.move_lines.mapped('product_id'):
                sfp_picks = sfp_pick
                break
        incomming_date = False
        if sfp_picks:
            incomming_date = sfp_picks[:1].date_done
        item.write({
            'in_date': incomming_date,
            'completed': all(
                pick.state in ['done', 'cancel'] for pick in sfp_pick),
        })
