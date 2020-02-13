# -*- coding: utf-8 -*-
# © 2019 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _get_last_move_id(self, move):
        def recursive_move(last_move):
            if not last_move.move_dest_ids:
                return last_move
            else:
                last_move = recursive_move(last_move.move_dest_ids)
            return last_move

        last_move = move.move_dest_ids
        return recursive_move(last_move)

    def _prepare_mo_vals(self, product_id, product_qty,
                         product_uom, location_id, name, origin, values, bom):
        res = super(StockRule, self)._prepare_mo_vals(
            product_id, product_qty, product_uom,
            location_id, name, origin, values, bom)
        last_move = self._get_last_move_id(values.get('move_dest_ids'))
        if last_move and last_move.sale_line_id:
            sale_line = last_move.sale_line_id
            last_sequence = sale_line.sequence - 1
            note_line = sale_line.search(
                [('order_id', '=', sale_line.order_id.id),
                 ('display_type', '=', 'line_note'),
                 ('sequence', '=', last_sequence)])
            if not note_line:
                note_line = sale_line.search(
                    [('order_id', '=', sale_line.order_id.id),
                     ('display_type', '=', 'line_note'),
                     ('id', '=', sale_line.id - 1)])
            res['sale_notes'] = note_line.name
        return res
