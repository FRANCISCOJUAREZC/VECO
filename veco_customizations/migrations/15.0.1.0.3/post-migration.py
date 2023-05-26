# -*- coding: utf-8 -*-
# Copyright 2022 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import datetime
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    stock_valuation_layers = env['stock.valuation.layer'].search([])
    layers_count = 0
    for layer in stock_valuation_layers:
        layers_count += 1
        _logger.info(
            'Layer %s of %s ---' %
            (layers_count, len(stock_valuation_layers)))
        if layer.unit_cost and layer.quantity and layer.value:
            continue
        if layer.quantity and not layer.unit_cost:
            value = abs(layer.account_move_id.line_ids[:1].balance)
            unit_cost = value / layer.quantity
            layer.write({
                'unit_cost': unit_cost,
                'value': unit_cost * layer.quantity,
            })
        if layer.quantity and layer.unit_cost and not layer.value:
            layer.write({
                'value': layer.unit_cost * layer.quantity,
            })
