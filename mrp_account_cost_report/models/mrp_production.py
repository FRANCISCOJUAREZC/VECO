# -*- coding: utf-8 -*-
# © 2021 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging


from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)


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
    # x_studio_cliente_p_1 = fields.Many2one(
    #    'res.partner',)
    x_studio_cliente_p_1 = fields.Char()

    @api.depends('state')
    def _compute_costs(self):
        # Guard against recursive recompute triggered by auditlog intercepting write()
        if self.env.context.get('_computing_mrp_costs'):
            return
        # Skip during SO confirmation BOM explosion; will recompute on MRP state change
        if self.env.context.get('_skip_mrp_cost_compute'):
            return
        self = self.with_context(_computing_mrp_costs=True)
        _logger.info("MRP _compute_costs: computing %s records", len(self))

        # 1. Build per-record backorder metadata in a single ORM pass
        rec_meta = {}
        all_component_pids = set()
        for rec in self:
            if 'procurement_group_id' in rec._fields and rec.procurement_group_id:
                backorders = rec.procurement_group_id.mrp_production_ids
            else:
                backorders = rec
            if backorders and rec.product_tracking in ['lot', 'serial']:
                component_pids = backorders.ids
            else:
                component_pids = rec.ids
            rec_meta[rec.id] = {
                'backorders': backorders,
                'component_pids': component_pids,
            }
            all_component_pids.update(component_pids)

        all_component_pids = list(all_component_pids)
        all_rec_ids = self.ids

        # 2. SQL: components amount grouped by production_id (no ORM object loading)
        components_by_pid = {}
        if all_component_pids:
            has_scrapped = 'scrapped' in self.env['stock.move']._fields
            scrapped_join = "AND sm.scrapped = false" if has_scrapped else ""
            scrapped_sm = "AND scrapped = false" if has_scrapped else ""
            if 'stock.valuation.layer' in self.env.registry:
                self.env.cr.execute("""
                    SELECT sm.raw_material_production_id,
                           COALESCE(SUM(ABS(svl.value)), 0)
                    FROM stock_valuation_layer svl
                    JOIN stock_move sm ON svl.stock_move_id = sm.id
                    WHERE sm.raw_material_production_id = ANY(%s)
                      AND sm.state != 'cancel'
                      AND sm.product_qty != 0 """ + scrapped_join + """
                    GROUP BY sm.raw_material_production_id
                """, [all_component_pids])
            else:
                self.env.cr.execute("""
                    SELECT raw_material_production_id,
                           COALESCE(SUM(ABS(product_qty * price_unit)), 0)
                    FROM stock_move
                    WHERE raw_material_production_id = ANY(%s)
                      AND state != 'cancel'
                      AND product_qty != 0 """ + scrapped_sm + """
                    GROUP BY raw_material_production_id
                """, [all_component_pids])
            components_by_pid = dict(self.env.cr.fetchall())

        # 3. SQL: total hours per production_id (all time_ids)
        hours_by_pid = {}
        if all_rec_ids:
            self.env.cr.execute("""
                SELECT wo.production_id, COALESCE(SUM(wt.duration) / 60.0, 0)
                FROM mrp_workcenter_productivity wt
                JOIN mrp_workorder wo ON wt.workorder_id = wo.id
                WHERE wo.production_id = ANY(%s)
                GROUP BY wo.production_id
            """, [all_rec_ids])
            hours_by_pid = dict(self.env.cr.fetchall())

        # 4. SQL: workforce & indirects per production_id using LATERAL window
        #    line_ids[0] = workforce (rn=1), line_ids[1] = indirects (rn=2)
        workforce_by_pid = {}
        if all_rec_ids:
            self.env.cr.execute("""
                SELECT
                    wo.production_id,
                    COALESCE(SUM(CASE WHEN aml.rn = 1 THEN ABS(aml.balance) END), 0),
                    COALESCE(SUM(CASE WHEN aml.rn = 2 THEN ABS(aml.balance) END), 0)
                FROM mrp_workcenter_productivity wt
                JOIN mrp_workorder wo ON wt.workorder_id = wo.id
                LEFT JOIN LATERAL (
                    SELECT balance,
                           ROW_NUMBER() OVER (ORDER BY sequence, id) AS rn
                    FROM account_move_line
                    WHERE move_id = wt.workforce_entry_id
                ) aml ON TRUE
                WHERE wo.production_id = ANY(%s)
                  AND wt.workforce_entry_id IS NOT NULL
                GROUP BY wo.production_id
            """, [all_rec_ids])
            for row in self.env.cr.fetchall():
                workforce_by_pid[row[0]] = (float(row[1]), float(row[2]))

        # 5. Per-record computation from pre-fetched SQL data
        for rec in self:
            meta = rec_meta[rec.id]
            backorders = meta['backorders']
            component_pids = meta['component_pids']

            components_amount = sum(
                components_by_pid.get(pid, 0.0) for pid in component_pids)
            hours = hours_by_pid.get(rec.id, 0.0)
            workforce_amount, indirects_amount = workforce_by_pid.get(
                rec.id, (0.0, 0.0))

            # Fallback: use stored values from backorders when rec has no time data
            if float_is_zero(workforce_amount, precision_digits=2) and backorders:
                workforce_amount = max(backorders.mapped('workforce_amount'))
                hours = max(backorders.mapped('hours'))
                indirects_amount = max(backorders.mapped('indirects_amount'))

            to_write = {
                'components_amount': components_amount,
                'workforce_amount': workforce_amount,
                'indirects_amount': indirects_amount,
                'hours': hours,
            }
            for field, field_value in to_write.items():
                if float_is_zero(field_value, precision_digits=2):
                    to_write[field] = rec._get_most_repeated_field_value(field)

            total_cost = (
                to_write['components_amount'] + to_write['workforce_amount'] +
                to_write['indirects_amount'])
            total_qty = (
                sum(backorders.mapped('product_qty')) if backorders
                else rec.product_qty
            ) or 1
            to_write['total_cost'] = total_cost
            to_write['unit_cost'] = total_cost / total_qty

            rec.update(to_write)

    def _get_most_repeated_field_value(self, field):
        self.ensure_one()
        try:
            self.env.cr.execute("""
                SELECT {field}, COUNT(*) AS cnt
                FROM mrp_production
                WHERE product_id = %s
                  AND state = 'done'
                  AND {field} > 0
                GROUP BY {field}
                ORDER BY cnt DESC
                LIMIT 1
            """.format(field=field), (self.product_id.id,))
            row = self.env.cr.fetchone()
            return row[0] if row else 0
        except Exception:
            return 0

    @api.depends('state', 'unit_cost', 'x_studio_sale_id')
    def _compute_sale_amount(self):
        # Skip during SO confirmation BOM explosion; will recompute on MRP state change
        if self.env.context.get('_skip_mrp_cost_compute'):
            return
        _logger.info(
            "MRP _compute_sale_amount: computing %s records", len(self))
        self.update({'sale_price_unit': 0.0, 'sale_amount': 0.0, 'factor': 0.0})
        valid_recs = self.filtered(lambda r: r.product_id and r.x_studio_sale_id)
        if not valid_recs:
            return
        product_ids = [r.product_id.id for r in valid_recs]
        order_ids = [r.x_studio_sale_id.id for r in valid_recs]
        self.env.cr.execute("""
            SELECT
                sol.product_id,
                sol.order_id,
                SUM(sol.price_subtotal)               AS total_subtotal,
                COALESCE(SUM(sol.product_uom_qty), 0) AS total_qty
            FROM sale_order_line sol
            WHERE sol.product_id = ANY(%s)
              AND sol.order_id   = ANY(%s)
            GROUP BY sol.product_id, sol.order_id
        """, [product_ids, order_ids])
        data = {
            (row[0], row[1]): (row[2], row[3])
            for row in self.env.cr.fetchall()
        }
        for rec in valid_recs:
            key = (rec.product_id.id, rec.x_studio_sale_id.id)
            total_subtotal, total_qty = data.get(key, (0.0, 0.0))
            sale_price_unit = total_subtotal / (total_qty or 1)
            rec.sale_price_unit = sale_price_unit
            rec.sale_amount = total_subtotal
            rec.factor = sale_price_unit / (rec.unit_cost or 1)

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
            rec.qty_done = sum(rec.finished_move_line_ids.mapped('quantity'))

    def refresh_costs(self):
        init_date = fields.Datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0)
        end_date = fields.Datetime.now().replace(
            hour=23, minute=59, second=59)
        orders = self.search([
            ('date_finished', '>=', init_date),
            ('date_planned_finished', '<=', end_date),
            ('state', '=', 'done')])
        orders._compute_costs()
