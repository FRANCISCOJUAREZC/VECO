
# -*- coding: utf-8 -*-
from xml import dom
from odoo import api, fields, models
from odoo import tools
from datetime import datetime
import re
import io
import base64


class ReporteProcutosXLS(models.AbstractModel):
    _name = 'report.bitsys_kardex_report.kardex_report_xlsx'
    _description = 'Reporte de Kardex'
    _inherit = 'report.report_xlsx.abstract'

    workbook = None
    
    def constructor(self,product_id=None, fecha_inicio=None,fecha_fin=None):
        producto=product_id
        inicio=fecha_inicio
        fin=fecha_fin

        dominio=[]
        if producto !=None:
            if len(producto)>0:
                dominio.append(('id','in',tuple(producto)))

        product_product=self.env['product.product'].search(dominio)
        # print("product_template",product_product)

        dominio=[('product_id','in',tuple(product_product.ids)),('picking_id.picking_type_id.code','in',('incoming','outgoing')),('picking_id.state','!=','cancel')]
        dom_ins_outs=[]
        # print("inicio",inicio,"fin",fin)
        if inicio !=False:
            dominio.append(('date','>=',inicio))
            dom_ins_outs.append(('date','<',inicio))
        if fin !=False:
            dominio.append(('date','<=',fin))
        stock_move_line=self.env['stock.move.line'].search(dominio)

        lista_kardex=[]
        for producto in product_product:
            stock=0
            if inicio !=False:
                dom_ins_outs.append(('product_id','=',producto.id))
                stock_a_fecha=self.env['stock.move.line'].search(dom_ins_outs)
                print("stock_a_fecha",stock_a_fecha)
                for sml in stock_a_fecha:
                    if sml.picking_id.picking_type_id.code =='incoming':
                        stock+=sml.qty_done
                    elif sml.picking_id.picking_type_id.code =='outgoing':
                        stock-=sml.qty_done
            # print("stock",stock)
            detalle=[]
            kardex={
                'codigo':producto.default_code,
                'producto':producto.name,
                'existencia': stock if inicio != False else producto.qty_available,
                'detalle':[],}
            # print("producto",producto.name)
            entrada=0
            salida=0
            existencia=0

            for sm in stock_move_line.filtered(lambda ml: ml.product_id.id==producto.id):
                entrada+=sm.qty_done if sm.picking_id.picking_type_id.code =='incoming' else 0
                salida+=sm.qty_done if sm.picking_id.picking_type_id.code =='outgoing' else 0
                existencia= entrada-salida
                # print("entrada",entrada,"salida",salida,"existencia",existencia,'stock',stock)
                linea={
                    'fecha':sm.date,
                    'lote':sm.lot_name if sm.lot_name else '',
                    'picking':sm.picking_id.name,
                    'estado':sm.picking_id.state,
                    'entrada':sm.qty_done if sm.picking_id.picking_type_id.code =='incoming' else 0,
                    'salida':sm.qty_done if sm.picking_id.picking_type_id.code =='outgoing' else 0,
                    'existencia':existencia + stock if inicio != False else existencia,
                }
                detalle.append(linea)
                # print("sm",sm.date, sm.picking_id.state, sm.picking_id.name, sm.product_id.name, sm.qty_done)
            kardex['detalle']=detalle
            if len(detalle)>0:
                lista_kardex.append(kardex)
        return lista_kardex



    def generate_xlsx_report(self, workbook, data, data_report):
        print("generate_xlsx_report")
        product_id = data['form']['product_id']
        fecha_inicio = data['form']['fecha_inicio']
        fecha_fin = data['form']['fecha_fin']

        kardex=self.constructor(product_id,fecha_inicio,fecha_fin)

        formato_titulo = workbook.add_format({'bold': 1,  'border': 0,    'align': 'center','valign':   'vcenter',      'fg_color': '#1C1C1C', 'font_color': 'white'})
        formato_titulo_general = workbook.add_format({'bold': 1,  'border': 0,    'align': 'center','valign':   'vcenter','font_size':   16, })
        formato_celda_numerica = workbook.add_format({'num_format': '#,##0.00', 'valign':   'vcenter', 'fg_color': 'white', 'border': 0, })
        formato_texto= workbook.add_format({'fg_color': 'white', 'border': 0, 'valign':   'vcenter'})
        formato_fecha= workbook.add_format({'num_format': 'dd/mm/yyyy'})

        sheet_libro = workbook.add_worksheet('Kardex')

        fila=0
        columna=-1

        sheet_libro.set_column(0,0, 15)
        sheet_libro.set_column(0,2, 20)
        sheet_libro.set_column(0,6, 20)

        inicio= fecha_inicio if fecha_inicio else ''
        fin= fecha_fin if fecha_fin else ''

        sheet_libro.merge_range( 'A1:G1','REPORTE DE KARDEX' if inicio =='' and fin =='' else 'REPORTE DE KARDEX DEL {} AL {}'.format(inicio ,fin) , formato_titulo_general)

        for producto in kardex:
            fila+=1
            titulo='[{}] {}   [EXISTENCIA]: {}'.format(producto['codigo'],producto['producto'],producto['existencia'])
            sheet_libro.merge_range( 'A{}:G{}'.format(fila+1,fila+1), titulo,formato_titulo)
            fila+=1
            sheet_libro.write(fila, 0,'FECHA',formato_titulo)
            sheet_libro.write(fila, 1,'LOTE',formato_titulo)
            sheet_libro.write(fila, 2,'PICKING',formato_titulo)
            sheet_libro.write(fila, 3,'ESTADO',formato_titulo)
            sheet_libro.write(fila, 4,'ENTRADA',formato_titulo)
            sheet_libro.write(fila, 5,'SALIDA',formato_titulo)
            sheet_libro.write(fila, 6,'EXISTENCIA',formato_titulo)

            for linea in producto['detalle']:
                fila+=1
                columna=columna+1

                sheet_libro.write(fila, columna, linea['fecha'],formato_fecha)
                sheet_libro.write(fila, columna+1, linea['lote'],formato_texto)
                sheet_libro.write(fila, columna+2, linea['picking'],formato_texto)
                sheet_libro.write(fila, columna+3, linea['estado'],formato_texto)
                sheet_libro.write(fila, columna+4, linea['entrada'],formato_celda_numerica)
                sheet_libro.write(fila, columna+5, linea['salida'],formato_celda_numerica)
                sheet_libro.write(fila, columna+6, linea['existencia'],formato_celda_numerica)
                columna=-1
            fila+=1
        workbook.close()
