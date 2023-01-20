# -*- coding: utf-8 -*-
# Copyright 2022 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    StockValuationLayer = env['stock.valuation.layer']
    seen = env['mrp.production']
    moves = env['stock.move'].search(
        [('stock_valuation_layer_ids', '=', False),
         ('state', '=', 'done'),
         ('raw_material_production_id', '!=', False)])
    count = 1
    for move in moves:
        _logger.info('Move %s of %s' % (count, len(moves)))
        count += 1
        order = move.raw_material_production_id
        svl = StockValuationLayer.search([
            ('description', '=', order.name.split('-')[0]),
            ('quantity', '=', -move.quantity_done),
            ('product_id', '=', move.product_id.id)], limit=1)
        if not svl:
            svl = StockValuationLayer.search([
                ('description', '=', order.name.split('-')[0]),
                ('product_id', '=', move.product_id.id)], limit=1)
        svl.stock_move_id = move.id
        seen |= move.raw_material_production_id

    _logger.info('Total Orders Procesed: %s' % (len(seen)))
