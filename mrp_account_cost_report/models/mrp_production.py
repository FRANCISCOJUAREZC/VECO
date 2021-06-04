# -*- coding: utf-8 -*-
# © 2021 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.addons import decimal_precision as dp
from odoo import api, fields, models


class MRPProduction(models.Model):
    _inherit = 'mrp.production'

    components_amount = fields.Float(
        compute='_compute_costs',
        store=True,
    )
    workforce_amount = fields.Float(
        compute='_compute_costs',
        store=True,
    )
    indirects_amount = fields.Float(
        compute='_compute_costs',
        store=True,
    )
    hours = fields.Float(
        compute='_compute_costs',
        store=True,
    )
    total_cost = fields.Float(
        compute='_compute_costs',
        store=True,
    )
    unit_cost = fields.Float(
        compute='_compute_costs',
        store=True,
    )
    sale_amount = fields.Float(
        compute='_compute_sale_amount',
        store=True,
    )
    sale_price_unit = fields.Float(
        compute='_compute_sale_amount',
        store=True,
    )
    components_percentage = fields.Float(
        compute='_compute_cost_percentages',
        store=True,
    )
    workforce_percentage = fields.Float(
        compute='_compute_cost_percentages',
        store=True,
    )
    indirects_percentage = fields.Float(
        compute='_compute_cost_percentages',
        store=True,
    )
    qty_done = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_qty_done', store=True,)
    factor = fields.Float(
        compute='_compute_sale_amount',
        store=True,
    )

    @api.depends('state')
    @api.multi
    def _compute_costs(self):
        for rec in self:
            to_write = {
                'components_amount': 0.0,
                'workforce_amount': 0.0,
                'indirects_amount': 0.0,
                'hours': 0.0,
            }
            # Components
            query_str = """SELECT abs(SUM(value))
                            FROM stock_move WHERE raw_material_production_id
                            IN %s AND state != 'cancel' AND product_qty != 0
                            AND scrapped != 't'
                        """
            self.env.cr.execute(query_str, (tuple(rec.ids), ))
            for cost in self.env.cr.fetchall():
                if cost and isinstance(cost[0], float):
                    to_write['components_amount'] += cost[0]

            # Workforce
            Workorders = self.env['mrp.workorder'].search(
                [('production_id', 'in', rec.ids)])
            for work_line in Workorders.mapped('time_ids'):
                if work_line.workforce_entry_id.line_ids:
                    to_write['workforce_amount'] += abs(
                        work_line.workforce_entry_id.line_ids[0].balance)
                    to_write['indirects_amount'] += abs(
                        work_line.workforce_entry_id.line_ids[1].balance)
                to_write['hours'] += (work_line.duration / 60)
            to_write['total_cost'] = (
                to_write['components_amount'] + to_write['workforce_amount'] +
                to_write['indirects_amount'])
            to_write['unit_cost'] = to_write['total_cost'] / (sum(rec.finished_move_line_ids.mapped('qty_done')) or 1)
            rec.update(to_write)

    @api.depends('state')
    @api.multi
    def _compute_sale_amount(self):
        for rec in self:
            lines = self.env['sale.order.line'].search(
                [('product_id', '=', rec.product_id.id),
                 ('order_id', '=', rec.x_studio_sale_id.id)])
            rec.update({
                'sale_price_unit': sum(lines.mapped('price_subtotal')) / (sum(
                    lines.mapped('product_uom_qty')) or 1),
                'sale_amount': sum(lines.mapped('price_subtotal')),
                'factor': sum(lines.mapped('price_subtotal')) / (rec.total_cost or 1),
            })

    @api.depends('components_amount', 'workforce_amount', 'indirects_amount')
    @api.multi
    def _compute_cost_percentages(self):
        for rec in self:
            rec.update({
                'components_percentage': rec.components_amount * 100 / (
                    rec.total_cost or 1),
                'workforce_percentage': rec.workforce_amount * 100 / (
                    rec.total_cost or 1),
                'indirects_percentage': rec.indirects_amount * 100 / (
                    rec.total_cost or 1),
            })

    @api.depends('state', 'finished_move_line_ids')
    def _compute_qty_done(self):
        for rec in self:
            rec.qty_done = sum(rec.finished_move_line_ids.mapped('qty_done'))
