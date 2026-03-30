# -*- coding: utf-8 -*-

from odoo import models,_
from odoo.exceptions import UserError
from datetime import date, datetime
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def create_cfdi_traslado(self):
        line_vals = []
        is_product = False
        cfdi_traslado_obj = self.env['cfdi.traslado']
        origin = ''
        for data in self:
            if data.state == 'assigned':
               if data.move_ids_without_package:
                   for line in data.move_ids_without_package:
                       for l in line_vals:
                           if l.get('product_id') == line.product_id.id:
                               is_product = True
                               l.update({'quantity': l.get('quantity') + line.quantity})
                       if not is_product:
                           if line.quantity > 0:
                              line_vals.append({'product_id':line.product_id.id,
                                                'name':line.product_id.partner_ref,
                                                'price_unit':line.product_id.lst_price,
                                                'pesoenkg':line.product_id.weight * line.quantity,
                                                'quantity':line.quantity})
                       is_product = False
                       origin += data.name + ' ' if not data.name in origin else ''
               else:
                   raise UserError(_('Debe tener productos en las líneas.'))
            if data.state == 'done':
               if data.move_ids_without_package:
                   for line in data.move_ids_without_package:
                       for l in line_vals:
                           if l.get('product_id') == line.product_id.id:
                               is_product = True
                               l.update({'quantity': l.get('quantity') + line.quantity})
                       if not is_product:
                           if line.quantity > 0:
                              line_vals.append({'product_id':line.product_id.id,
                                                'name':line.product_id.partner_ref,
                                                'price_unit':line.product_id.lst_price,
                                                'pesoenkg':line.product_id.weight * line.quantity,
                                                'quantity':line.quantity})
                       is_product = False
                       origin += data.name + ' ' if not data.name in origin else ''
               else:
                   raise UserError(_('Debe tener productos en las líneas.'))

        if line_vals:
               val = {
                   'partner_id': self.company_id.partner_id.id, #data.company_id.id,
                   'source_document': origin,
                   'invoice_date': datetime.today(),
                   'currency_id': self.company_id.currency_id.id, # data.company_id.currency_id.id,
                   'factura_line_ids':line_vals and [(0,0,i) for i in line_vals] or [(0,0,{})],
                   'company_id': self.company_id.id,
                   'journal_id': self.env['account.journal'].search([('type','=','sale'),('company_id', '=', self.company_id.id)],limit=1).id,
                   }
               cfdi_id = cfdi_traslado_obj.create(val)
        else:
               raise UserError(_('Solo se pueden crear un CFDI de traslado si el documento está reservado o hecho.'))
        return True
