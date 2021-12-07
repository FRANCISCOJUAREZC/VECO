from odoo import models,_
from odoo.exceptions import UserError
from datetime import date, datetime

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def create_cfdi_traslado(self):
        line_vals = []
        is_product = False
        cfdi_traslado_obj = self.env['cfdi.traslado']
        for data in self:
            if data.move_ids_without_package:
                for line in data.move_ids_without_package:
                    for l in line_vals:
                        if l.get('product_id') == line.product_id.id:
                            is_product = True
                            l.update({'quantity': l.get('quantity') + line.reserved_availability})
                    if not is_product:
                        line_vals.append({'product_id':line.product_id.id,
                                          'name':line.product_id.partner_ref,
                                          'price_unit':line.product_id.lst_price,
                                          'pesoenkg':line.product_id.weight * line.reserved_availability,
                                          'quantity':line.reserved_availability})
                    is_product = False
            else:
                raise UserError(_('Please select product line.'))
            val = {
                'partner_id': self.env.user.company_id.id,
                'source_document':data.name,
                'invoice_date': datetime.today(),
                'currency_id': self.env.user.company_id.currency_id.id,
                'factura_line_ids':line_vals and [(0,0,i) for i in line_vals] or [(0,0,{})],
                }
            cfdi_id = cfdi_traslado_obj.create(val)
        return True  
