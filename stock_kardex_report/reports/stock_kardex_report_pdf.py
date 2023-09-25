# -*- coding: utf-8 -*-
from odoo import api, fields, models

class StockKardexReportPDF(models.AbstractModel):
    _name = 'report.stock_kardex_report.stock_kardex_report_pdf'
    _description = 'Kárdex de inventario'

    def _get_report_values(self, docids, data=None):
        company_id = self.env.company
        docs = self.env['stock.kardex.report.wiz'].browse(docids)
        records = self.env['stock.kardex.report'].search([('company_id', '=', company_id.id)])
        return {
            'docs' : docs,
            'records': records
        }