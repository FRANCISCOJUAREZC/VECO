# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import xml.etree.ElementTree as gfg
import os
import io
import re
import base64
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    veco_agregada = fields.Boolean(string='Adenda OC', readonly=True, default=False)

    def action_add_addenda_oc(self):
        if not self.veco_agregada:
           xml_file = self.l10n_mx_edi_cfdi_attachment_id
           if not xml_file:
              raise UserError(_('La factura aún no tiene un XML timbrado.'))

           if not self.ref:
               raise UserError(_('Falta especificar la OC.'))

           root = gfg.Element("cfdi:Addenda")

           b1 = gfg.Element("PO")
           b1.text = str(self.ref)
           root.append(b1)

           if xml_file:
                try:
                    filedata = ''
                    # Read in the file
                    cfdi_data = base64.decodebytes(xml_file.with_context(bin_size=False).datas).decode()
                    if not "cfdi:Addenda" in cfdi_data:
                       # Replace the target string
                       filedata = cfdi_data.replace('</cfdi:Comprobante>', gfg.tostring(root).decode() +'</cfdi:Comprobante>')
                       # Write the file out again
                       text = base64.encodebytes(filedata.encode('utf-8'))
                       xml_file.write({
                         'datas': text,
                         'mimetype': 'application/xml'
                       })
                    self.veco_agregada = True
                except Exception as e:
                    _logger.error(str(e))
                    pass
