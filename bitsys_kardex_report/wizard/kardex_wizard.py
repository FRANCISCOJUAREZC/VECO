# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo import tools
import datetime
import io
import base64
class KardexReport(models.TransientModel):
    _name = "bitsys_kardex_report.kardex.report"
    _description = "Reporte de Kardex"
    # _inherit = 'product.template'


    product_id = fields.Many2many('product.product',string='Producto',domain="[('detailed_type','=','product')]")
    fecha_inicio = fields.Date(string="Fecha Inicio")
    fecha_fin = fields.Date(string="Fecha Fin")

    def _build_contexts(self, data):
        result = {}
        result['product_id'] = data['form']['product_id'] or False
        result['fecha_inicio'] = data['form']['fecha_inicio'] or False
        result['fecha_fin'] = data['form']['fecha_fin'] or False
        return result

    def export_xls(self):
        print("export_xls")
        self.ensure_one()
        data = {}
        data['form'] = self.read(['product_id','fecha_inicio','fecha_fin'])[0]
        print("data",data)

        return self.env['ir.actions.report'].search([('report_name', '=', 'bitsys_kardex_report.kardex_report_xlsx'),('report_type', '=', 'xlsx')], limit=1).report_action(self, data=data)

