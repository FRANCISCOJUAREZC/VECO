# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from codecs import BOM_UTF8
from datetime import date
from time import mktime

from lxml import objectify
from lxml.etree import XMLSyntaxError
from odoo import _, api, fields, models
from odoo.exceptions import UserError

BOM_UTF8U = BOM_UTF8.decode('UTF-8')


class ResCompany(models.Model):
    _inherit = 'res.company'

    xunnel_last_sync = fields.Date(string='Last Sync with Xunnel', default=lambda _: date.today())

    @api.model
    def l10n_mx_edi_get_tfd_etree(self, cfdi):
        """Get the TimbreFiscalDigital node from the cfdi.

        :param cfdi: The cfdi as etree
        :return: the TimbreFiscalDigital node
        """
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    def _sync_xunnel_documents(self):
        """Requests https://wwww.xunnel.com/ to retrive all invoices
        related to the current company and check them in the database
        to create them if they're not. After refresh xunnel_last_sync
        """
        self.ensure_one()
        if not self.vat and self.xunnel_token:
            raise UserError(_('You need to define the VAT of your company.'))
        values = dict(
            last_sync=False,
            xunnel_testing=False,
            vat=self.vat)
        if self.xunnel_last_sync:
            values.update(last_sync=mktime(self.xunnel_last_sync.timetuple()))
        response = self._xunnel('get_invoices_sat', values)
        err = response.get('error')
        if err:
            raise UserError(err)
        if response.get('response') is None:
            return True
        dates = []
        failed = 0
        created = []
        folder_id = self.env.ref('documents.documents_finance_folder')
        for item in response.get('response'):
            xml = item.lstrip(BOM_UTF8U).encode("UTF-8")
            try:
                xml = xml.replace(b'xmlns:schemaLocation', b'xsi:schemaLocation')
                xml_obj = objectify.fromstring(xml)
            except XMLSyntaxError:
                failed += 1
                continue
            dates.append(xml_obj.get('Fecha', xml_obj.get('fecha', ' ')))
            uuid = self.l10n_mx_edi_get_tfd_etree(xml_obj).get('UUID')
            datas_fname = "%s.xml" % (uuid)
            document = self.env['documents.document'].search([('name', '=', datas_fname), ('name', '!=', False)])
            if not document:
                document = document.with_context(xml_obj=xml_obj, no_document=True).create({
                    'name': datas_fname,
                    'xunnel_document': True,
                    'type': 'binary',
                    'datas': base64.b64encode(bytes(xml)),
                    'index_content': xml,
                    'mimetype': 'application/xml',
                    'folder_id': folder_id.id,
                })
                created.append(document.id)
        self.xunnel_last_sync = max(dates) if dates else self.xunnel_last_sync
        return {
            'created': created,
            'failed': failed,
        }

    def get_xml_sync_action(self):
        result = self._sync_xunnel_documents()
        message_class = 'success'
        message = _(
            "%s xml have been downloaded.") % result.get('created')
        failed = result.get('failed')
        if failed:
            message_class = 'warning'
            message += _(
                "\nAlso %s files have failed at the conversion."
                "\nWe sent you an email with the details of the failed invoices.") % failed
        action_params = {'message': message, 'message_class': message_class}
        return {
            'type': 'ir.actions.client',
            'tag': 'account_xunnel.synchronized_accounts',
            'name': _('Xunnel invoice response.'),
            'target': 'new',
            'params': action_params,
        }
