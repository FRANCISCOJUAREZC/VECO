# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import xml.etree.ElementTree as gfg
import os
import io
import base64
import re
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    veco_agregada = fields.Boolean(string='Adenda OC', readonly=True, default=False)

    def action_add_addenda_oc(self):
        if not self.veco_agregada:

           if not self.ref:
               raise UserError(_('Falta especificar la OC.'))

           if not self._get_l10n_mx_edi_signed_edi_document():
               raise UserError(_('Se debe timbrar primero la factura.'))

           root = gfg.Element("cfdi:Addenda")
#           nsmap = {
#             None: "http://tempuri.org/DSCargaRemisionProv.xsd",
#           }
#           m1 = gfg.Element('DSCargaRemisionProv', xmlns="http://tempuri.org/DSCargaRemisionProv.xsd")
#           root.append (m1)

           b1 = gfg.Element("PO")
           b1.text = str(self.ref)
           root.append(b1)

           xml_file = self._get_l10n_mx_edi_signed_edi_document()

           if xml_file:
                #_logger.info('pasa 01')
                try:
                    filedata = ''
                    # Read in the file
                    cfdi_data = base64.decodebytes(xml_file.attachment_id.with_context(bin_size=False).datas).decode()

                    # Replace the target string
                    filedata = cfdi_data.replace('</cfdi:Comprobante>', gfg.tostring(root).decode() +'</cfdi:Comprobante>')

                    # Write the file out again
                    text = base64.encodebytes(filedata.encode('utf-8'))
                    xml_file.attachment_id.write({
                      'datas': text,
                      'mimetype': 'application/xml'
                    })
                    self.veco_agregada = True
                except Exception as e:
                    _logger.error(str(e))
                    pass
