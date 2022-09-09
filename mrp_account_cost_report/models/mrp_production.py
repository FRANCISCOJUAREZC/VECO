# -*- coding: utf-8 -*-
# © 2021 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

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
        digits='Product Unit of Measure',
        compute='_compute_qty_done', store=True,)
    factor = fields.Float(
        compute='_compute_sale_amount',
        store=True,
    )

    @api.depends('state')
    def _compute_costs(self):
        for rec in self:
            to_write = {
                'components_amount': 0.0,
                'workforce_amount': 0.0,
                'indirects_amount': 0.0,
                'hours': 0.0,
            }
            # Components
            raw_material_moves = []
            currency_table = self.env['res.currency']._get_query_currency_table({
                'multi_company': True,
                'date': {
                    'date_to': fields.Date.today()}
                })
            query_str = """SELECT
                                sm.product_id,
                                mo.id,
                                abs(SUM(svl.quantity)),
                                abs(SUM(svl.value)),
                                currency_table.rate
                             FROM stock_move AS sm
                       INNER JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                       LEFT JOIN mrp_production AS mo on sm.raw_material_production_id = mo.id
                       LEFT JOIN {currency_table} ON currency_table.company_id = mo.company_id
                            WHERE sm.raw_material_production_id in %s AND sm.state != 'cancel' AND sm.product_qty != 0 AND scrapped != 't'
                         GROUP BY sm.product_id, mo.id, currency_table.rate""".format(currency_table=currency_table,)
            self.env.cr.execute(query_str, (tuple(rec.ids), ))
            total_cost = 0
            for product_id, mo_id, qty, cost, currency_rate in self.env.cr.fetchall():
                cost *= currency_rate
                to_write['components_amount'] += cost

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
