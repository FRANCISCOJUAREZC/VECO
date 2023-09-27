# -*- coding: utf-8 -*-
from odoo import models
from pytz import timezone

class ExportXLSX(models.AbstractModel):
    _name = 'report.stock_kardex_report.stock_kardex_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Kárdex de inventario en xlsx"

    def generate_xlsx_report(self, workbook, data, lines):
        company_id = lines.company_id
        user_tz = self.env.user.tz
        date_from = lines.date_from.astimezone(timezone(user_tz))
        date_to = lines.date_to.astimezone(timezone(user_tz))
        kardex_lines = self.env["stock.kardex.report"].search([('company_id','=',company_id.id)])
        hide_header = lines.hide_header
        column_format = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'font_color': '#ba8328', 'border': 1})
        left_column = workbook.add_format({'font_size': 11, 'align': 'left', 'bold': True, 'font_color': '#ba8328', 'bg_color': "#F8F8F8", 'border': 1})
        header_format = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True, 'border': 1})
        sub_header = workbook.add_format({'font_size': 12, 'align': 'center'})
        center_format = workbook.add_format({'font_size': 10, 'align': 'center'})
        left_format = workbook.add_format({'font_size': 10, 'align': 'left'})
        right_format =workbook.add_format({'font_size': 10, 'align': 'right'})
        right_format_monetary = workbook.add_format({'font_size': 10, 'align': 'right', 'num_format': '$#,##0.00'})

        sheet = workbook.add_worksheet('Kárdex de inventario')

        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 50)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 21)
        sheet.set_column('F:F', 21)
        sheet.set_column('G:G', 25)
        sheet.set_column('H:H', 10)
        sheet.set_column('I:I', 10)
        sheet.set_column('J:J', 10)
        sheet.set_column('K:K', 10)
        sheet.set_column('L:L', 10)

        sheet.merge_range('A1:L1', 'Kárdex de inventario', header_format)
        sheet.merge_range('A2:L2', 'Generado de: {} a {}'.format(date_from.strftime("%Y-%m-%d %H:%M:%S"), date_to.strftime("%Y-%m-%d %H:%M:%S")), sub_header)
        sheet.write('A3', 'Fecha', column_format)
        sheet.write('B3', 'Origen', column_format)
        sheet.write('C3', 'Producto', column_format)
        sheet.write('D3', 'Unidad', column_format)
        sheet.write('E3', 'Ubicación origen', column_format)
        sheet.write('F3', 'Ubicación destino', column_format)
        sheet.write('G3', 'Lote/N° de serie', column_format)
        sheet.write('H3', 'Inicial', column_format)
        sheet.write('I3', 'Hecho', column_format)
        sheet.write('J3', 'Final', column_format)
        sheet.write('K3', 'Costo', column_format)
        sheet.write('L3', 'Valor final', column_format)

        row = 4
        col = 0
        locations = set(kardex_lines.mapped('group_name'))
        for location in locations:
            if not hide_header:
                range = 'A{}:L{}'.format(row, row)
                sheet.merge_range(range, location, left_column)
                row += 1
            for kardex_line in kardex_lines.filtered(lambda line: line.group_name == location).sorted('date', reverse=False):
                date = kardex_line.date.strftime("%Y-%m-%d %H:%M:%S")
                sheet.write(row-1, col, date, center_format)
                sheet.write(row-1, col+1, str(kardex_line.origin).replace("False",""), center_format)
                sheet.write(row-1, col+2, str(kardex_line.product_id.display_name).replace("False",""), left_format)
                sheet.write(row-1, col+3, str(kardex_line.product_uom_id.name).replace("False",""), center_format)
                sheet.write(row-1, col+4, str(kardex_line.location_id.name).replace("False",""), center_format)
                sheet.write(row-1, col+5, str(kardex_line.location_dest_id.name).replace("False",""), center_format)
                sheet.write(row-1, col+6, str(kardex_line.lot_id.name).replace("False",""), center_format)
                sheet.write(row-1, col+7, kardex_line.initial_balance, right_format)
                sheet.write(row-1, col+8, kardex_line.qty_done, right_format)
                sheet.write(row-1, col+9, kardex_line.balance, right_format)
                sheet.write(row-1, col+10, kardex_line.unit_cost, right_format_monetary)
                sheet.write(row-1, col+11, kardex_line.total_cost, right_format_monetary)
                row += 1
