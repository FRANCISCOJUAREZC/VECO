# -*- coding: utf-8 -*-
# © 2021 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


from odoo import tools
from odoo import api, fields, models


class ManufactureCostReport(models.Model):
    _name = "manufacture.cost.report"
    _description = "Manufacture Cost Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc, description'

    date = fields.Datetime(readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    description = fields.Char('Description', readonly=True)
    production_id = fields.Many2one(
        'mrp.production', 'Manufacture Order', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True)
    product_uom_qty = fields.Float('Quantity', readonly=True)
    # lot_id = fields.Many2one('stock.production.lot', 'Order/Sale', readonly=True) # Pendiente
    customer = fields.Char('Customer', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    # Totals
    components_amount = fields.Float('Components Total', readonly=True)
    workforce_amount = fields.Float('Workforce Total', readonly=True)
    hours = fields.Float('Hours', readonly=True)
    indirects_amount = fields.Float('Indirects Amount', readonly=True)

    components_percentage = fields.Float('Components %', readonly=True)
    workforce_percentage = fields.Float('Workforce %', readonly=True)
    indirects_percentage = fields.Float('Indirects %', readonly=True)
    total_percentage = fields.Float('Total %', readonly=True, default=100)

    price_subtotal = fields.Float('Subtotal', readonly=True)
    unit_cost = fields.Float('Unit Cost', readonly=True)
    sale_amount = fields.Float(readonly=True)
    price_unit = fields.Float('Price Unit', readonly=True)
    factor = fields.Float('Factor', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        select_ = """
            min(mp.id) as id,
            mp.date_finished as date,
            mp.product_id as product_id,
            mp.name as description,
            mp.id as production_id,
            mp.product_uom_id as product_uom_id,
            sum(mp.qty_done) as product_uom_qty,
            mp.x_studio_cliente_p_1 as customer,
            mp.company_id as company_id,
            SUM(mp.components_amount) as components_amount,
            SUM(mp.workforce_amount) as workforce_amount,
            SUM(mp.indirects_amount) as indirects_amount,
            SUM(mp.hours) as hours,
            SUM(mp.components_percentage) as components_percentage,
            SUM(mp.workforce_percentage) as workforce_percentage,
            SUM(100) as total_percentage,
            SUM(mp.indirects_percentage) as indirects_percentage,
            SUM(mp.total_cost) as price_subtotal,
            SUM(mp.unit_cost) as unit_cost,
            SUM(mp.sale_amount) as sale_amount,
            SUM(mp.sale_price_unit) as price_unit,
            SUM(mp.factor) as factor

        """

        for field in fields.values():
            select_ += field

        from_ = """
                mrp_production mp
                %s
        """ % from_clause

        groupby_ = """
            mp.product_id,
            mp.name,
            mp.product_uom_id,
            mp.date_finished,
            mp.company_id,
            mp.id,
            mp.components_amount,
            mp.workforce_amount,
            mp.indirects_amount,
            mp.hours,
            mp.x_studio_cliente_p_1
             %s
        """ % (groupby)

        return (
            "%s (SELECT %s FROM %s WHERE mp.state = 'done' GROUP BY %s)"
            % (with_, select_, from_, groupby_)
        )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (
            self._table, self._query()))
