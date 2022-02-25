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
            query_str = """
                SELECT
                    comp_cost.total * currency_table.rate  AS component_cost
            """
            query_str += """
                FROM mrp_production AS mo
                LEFT JOIN (
                    SELECT
                        mo.id                                                                    AS mo_id,
                        CASE WHEN SUM(svl.value) IS NULL THEN 0.0 ELSE abs(SUM(svl.value)) END   AS total
                    FROM mrp_production AS mo
                    LEFT JOIN stock_move AS sm on sm.raw_material_production_id = mo.id
                    LEFT JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                    WHERE mo.state = 'done'
                        AND (sm.state = 'done' or sm.state IS NULL)
                        AND (sm.scrapped != 't' or sm.scrapped IS NULL)
                    GROUP BY
                        mo.id
                ) comp_cost ON comp_cost.mo_id = mo.id
                LEFT JOIN (
                    SELECT
                        mo_id                                                                    AS mo_id,
                        SUM(op_costs_hour / 60. * op_duration)                                   AS total,
                        SUM(op_duration)                                                         AS total_duration
                    FROM (
                        SELECT
                            mo.id AS mo_id,
                            CASE
                                WHEN wo.costs_hour != 0.0 AND wo.costs_hour IS NOT NULL THEN wo.costs_hour
                                WHEN wc.costs_hour IS NOT NULL THEN wc.costs_hour
                                ELSE 0.0 END                                                                AS op_costs_hour,
                            CASE WHEN SUM(t.duration) IS NULL THEN 0.0 ELSE SUM(t.duration) END             AS op_duration
                        FROM mrp_production AS mo
                        LEFT JOIN mrp_workorder wo ON wo.production_id = mo.id
                        LEFT JOIN mrp_workcenter_productivity t ON t.workorder_id = wo.id
                        LEFT JOIN mrp_workcenter wc ON wc.id = t.workcenter_id
                        WHERE mo.state = 'done'
                        GROUP BY
                            mo.id,
                            wc.costs_hour,
                            wo.id
                        ) AS op_cost_vars
                    GROUP BY mo_id
                ) op_cost ON op_cost.mo_id = mo.id
                LEFT JOIN (
                    SELECT
                        mo.id AS mo_id,
                        CASE WHEN SUM(sm.cost_share) IS NOT NULL THEN SUM(sm.cost_share) / 100. ELSE 0.0 END AS byproduct_cost_share
                    FROM stock_move AS sm
                    LEFT JOIN mrp_production AS mo ON sm.production_id = mo.id
                    WHERE
                        mo.state = 'done'
                        AND sm.state = 'done'
                        AND sm.product_qty != 0
                        AND sm.scrapped != 't'
                    GROUP BY mo.id
                ) cost_share ON cost_share.mo_id = mo.id
                LEFT JOIN (
                    SELECT
                        mo.id AS mo_id,
                        SUM(sm.product_qty) AS product_qty
                    FROM stock_move AS sm
                    RIGHT JOIN mrp_production AS mo ON sm.production_id = mo.id
                     WHERE
                        mo.state = 'done'
                        AND sm.state = 'done'
                        AND sm.product_qty != 0
                        AND mo.product_id = sm.product_id
                    GROUP BY mo.id
                ) prod_qty ON prod_qty.mo_id = mo.id
                LEFT JOIN {currency_table} ON currency_table.company_id = mo.company_id
            """.format(currency_table=self.env['res.currency']._get_query_currency_table({'multi_company': True, 'date': {'date_to': fields.Date.today()}}))
            query_str += """
                WHERE
                    mo.state = 'done'
            """
            query_str += """
                GROUP BY
                    mo.id,
                    cost_share.byproduct_cost_share,
                    comp_cost.total,
                    op_cost.total,
                    op_cost.total_duration,
                    prod_qty.product_qty,
                    currency_table.rate
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
