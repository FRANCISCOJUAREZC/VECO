# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, models
from odoo.tools import float_round, SQL


class MrpCostStructure(models.AbstractModel):
    _inherit = 'report.mrp_account_enterprise.mrp_cost_structure'

    def get_lines(self, productions):
        ProductProduct = self.env['product.product']
        StockMove = self.env['stock.move']
        res = []
        # v18+: _get_query_currency_table eliminado → usar _get_simple_currency_table
        currency_table = self.env['res.currency']._get_simple_currency_table(self.env.companies)

        for product in productions.mapped('product_id'):
            mos = productions.filtered(lambda m: m.product_id == product)
            total_cost_by_mo = defaultdict(float)
            component_cost_by_mo = defaultdict(float)
            operation_cost_by_mo = defaultdict(float)

            # Get operations details + cost
            operations = []
            total_cost_operations = 0.0
            Workorders = self.env['mrp.workorder'].search([('production_id', 'in', mos.ids)])
            if Workorders:
                total_cost_operations = self._compute_mo_operation_cost(
                    currency_table, Workorders,
                    total_cost_by_mo, operation_cost_by_mo,
                    total_cost_operations, operations,
                )

            # Get the cost of raw material effectively used
            # v18+: SQL() object con parámetros nombrados y alias account_currency_table
            raw_material_moves = {}
            total_cost_components = 0.0
            query = SQL("""
                SELECT
                    sm.product_id,
                    mo.id,
                    abs(SUM(svl.quantity)),
                    abs(SUM(svl.value)),
                    account_currency_table.rate
                FROM stock_move AS sm
                INNER JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                LEFT JOIN mrp_production AS mo ON sm.raw_material_production_id = mo.id
                LEFT JOIN %(currency_table)s ON account_currency_table.company_id = mo.company_id
                WHERE sm.raw_material_production_id IN %(mos_ids)s
                    AND sm.state != 'cancel'
                    AND sm.product_qty != 0
                    AND scrapped != 't'
                GROUP BY sm.product_id, mo.id, account_currency_table.rate
            """,
                currency_table=currency_table,
                mos_ids=tuple(mos.ids),
            )
            self.env.cr.execute(query)
            for product_id, mo_id, qty, cost, currency_rate in self.env.cr.fetchall():
                cost *= currency_rate
                # v18+: deduplicar por product_id (antes era lista con posibles duplicados)
                if product_id in raw_material_moves:
                    raw_material_moves[product_id]['cost'] += cost
                    raw_material_moves[product_id]['qty'] += qty
                else:
                    raw_material_moves[product_id] = {
                        'qty': qty,
                        'cost': cost,
                        'product_id': ProductProduct.browse(product_id),
                    }
                total_cost_by_mo[mo_id] += cost
                component_cost_by_mo[mo_id] += cost
                total_cost_components += cost
            raw_material_moves = list(raw_material_moves.values())

            # Get the cost of scrapped materials
            # v18+: incluye tanto production_id como raw_material_production_id
            scraps = StockMove.search([
                '|',
                ('production_id', 'in', mos.ids),
                ('raw_material_production_id', 'in', mos.ids),
                ('scrapped', '=', True),
                ('state', '=', 'done'),
            ])

            # Get the byproducts and their total + avg per uom cost share amounts
            total_cost_by_product = defaultdict(float)
            qty_by_byproduct = defaultdict(float)
            qty_by_byproduct_w_costshare = defaultdict(float)
            component_cost_by_product = defaultdict(float)
            operation_cost_by_product = defaultdict(float)
            byproduct_moves = mos.move_byproduct_ids.filtered(lambda m: m.state != 'cancel')
            for move in byproduct_moves:
                # v18+: move.product_qty → conversión explícita con move.quantity
                qty = move.product_uom._compute_quantity(
                    move.quantity, move.product_id.uom_id, rounding_method='HALF-UP')
                qty_by_byproduct[move.product_id] += qty
                if move.cost_share != 0:
                    qty_by_byproduct_w_costshare[move.product_id] += qty
                    cost_share = move.cost_share / 100
                    total_cost_by_product[move.product_id] += total_cost_by_mo[move.production_id.id] * cost_share
                    component_cost_by_product[move.product_id] += component_cost_by_mo[move.production_id.id] * cost_share
                    operation_cost_by_product[move.product_id] += operation_cost_by_mo[move.production_id.id] * cost_share

            # Get product qty and its relative total + avg per uom cost share amount
            uom = product.uom_id
            mo_qty = 0
            for m in mos:
                cost_share = float_round(
                    1 - sum(m.move_finished_ids.mapped('cost_share')) / 100,
                    precision_rounding=0.0001,
                )
                total_cost_by_product[product] += total_cost_by_mo[m.id] * cost_share
                component_cost_by_product[product] += component_cost_by_mo[m.id] * cost_share
                operation_cost_by_product[product] += operation_cost_by_mo[m.id] * cost_share
                # v18+: product_uom_qty → conversión con move.quantity
                for move in m.move_finished_ids:
                    if move.state != 'done' or move.product_id != product:
                        continue
                    mo_qty += move.product_uom._compute_quantity(move.quantity, m.product_id.uom_id)

            res.append({
                'product': product,
                'mo_qty': mo_qty,
                'mo_uom': uom,
                'operations': operations,
                'currency': self.env.company.currency_id,
                'raw_material_moves': raw_material_moves,
                # v18+: total_cost_components y total_cost_operations como claves separadas
                'total_cost_components': total_cost_components,
                'total_cost_operations': total_cost_operations,
                'total_cost': total_cost_components + total_cost_operations,
                'scraps': scraps,
                'mocount': len(mos),
                'byproduct_moves': byproduct_moves,
                'component_cost_by_product': component_cost_by_product,
                'operation_cost_by_product': operation_cost_by_product,
                'qty_by_byproduct': qty_by_byproduct,
                'qty_by_byproduct_w_costshare': qty_by_byproduct_w_costshare,
                'total_cost_by_product': total_cost_by_product,
            })
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        productions = self.env['mrp.production']\
            .browse(docids)\
            .filtered(lambda p: p.state != 'cancel')
        res = None
        if all(production.state == 'done' for production in productions):
            res = self.get_lines(productions)
        return {'lines': res}
