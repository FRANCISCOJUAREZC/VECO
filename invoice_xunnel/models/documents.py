import base64
import json
import logging
from datetime import datetime

import requests
from lxml import objectify
from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_repr

CFDI_SAT_QR_STATE = {
    'No Encontrado': 'not_found',
    'Cancelado': 'cancelled',
    'Vigente': 'valid',
}

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _inherit = 'documents.document'

    sat_status = fields.Selection(
        selection=[
            ('none', 'State not defined'),
            ('undefined', 'Not Synced Yet'),
            ('not_found', 'Not Found'),
            ('cancelled', 'Cancelled'),
            ('valid', 'Valid'),
        ],
        compute='_compute_sat_status',
        default='undefined',
        store=True,
        help='Refers to the status of the invoice inside the SAT system.')
    emitter_partner_id = fields.Many2one(
        'res.partner',
        compute="_compute_emitter_partner_id",
        string="Emitter",
        help="In case this is a CFDI file, stores emitter's name.",
        store=True)
    xunnel_document = fields.Boolean(
        help="Specify if this is a XUNNEL document.")
    invoice_total_amount = fields.Float(
        string='Total Amount',
        compute="_compute_emitter_partner_id",
        help="In case this is a CFDI file, stores invoice's total amount.",
        store=True)
    stamp_date = fields.Datetime(
        compute="_compute_emitter_partner_id",
        help="In case this is a CFDI file, stores invoice's stamp date.",
        store=True)
    product_list = fields.Text(
        compute="_compute_product_list",
        string='Products',
        help="In case this is a CFDI file, show invoice's product list",
        store=True,
    )
    related_cfdi = fields.Text(
        compute="_compute_related_cfdi",
        string='Related CFDI',
        help="Related CFDI of the XML file",
        store=True,
    )

    @api.depends('datas')
    def _compute_emitter_partner_id(self):
        documents = self.filtered(
            lambda rec: rec.xunnel_document and rec.attachment_id)
        for rec in documents:
            xml = rec.get_xml_object(rec.datas)
            if xml is None:
                return
            rfc = xml.Emisor.get('Rfc', '').upper()
            name = xml.Emisor.get('Nombre', '').upper()
            partner = self.env['res.partner'].search([
                ('vat', '=', rfc)], limit=1)
            if not partner:
                partner = partner.create({
                    'vat': rfc,
                    'name': name,
                })
            stamp_date = xml.Complemento.xpath(
                'tfd:TimbreFiscalDigital[1]',
                namespaces={
                    'tfd':
                    'http://www.sat.gob.mx/TimbreFiscalDigital'})[0].get(
                        'FechaTimbrado')

            rec.emitter_partner_id = partner.id
            rec.invoice_total_amount = xml.get('Total')
            rec.stamp_date = datetime.strptime(stamp_date, "%Y-%m-%dT%H:%M:%S")

    @api.depends('datas')
    def _compute_sat_status(self):
        for rec in self:
            if not rec.xunnel_document:
                rec.sat_status = 'none'
                continue
            xml = rec.get_xml_object(rec.datas)
            if xml is not None:
                rec.sat_status = self.l10n_mx_edi_update_sat_status_xml(xml)
            else:
                rec.sat_status = 'none'

    def l10n_mx_edi_update_sat_status_xml(self, xml):
        """Check SAT WS to make sure the invoice is valid.
        inv: dict containing values to check SAT WS correctly.
        """
        template = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="http://tempuri.org/"
xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Consulta>
         <ns0:expresionImpresa>${data}</ns0:expresionImpresa>
      </ns0:Consulta>
   </ns1:Body>
</SOAP-ENV:Envelope>"""
        supplier_rfc = xml.Emisor.get('Rfc', '').upper()
        customer_rfc = xml.Receptor.get('Rfc', '').upper()
        amount = float(xml.get('Total', 0.0))
        uuid = xml.get('UUID', '')
        currency = self.env['res.currency'].search([('name', '=', xml.get('Moneda', 'MXN'))])
        precision = currency.decimal_places if currency else 0
        tfd = self.env['res.company'].l10n_mx_edi_get_tfd_etree(xml)
        uuid = tfd.get('UUID', '')
        total = float_repr(amount, precision_digits=precision)
        params = '?re=%s&amp;rr=%s&amp;tt=%s&amp;id=%s' % (
            tools.html_escape(tools.html_escape(supplier_rfc or '')),
            tools.html_escape(tools.html_escape(customer_rfc or '')),
            total or 0.0, uuid or '')
        soap_env = template.format(data=params)
        try:
            soap_xml = requests.post(
                'https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl',
                data=soap_env,
                timeout=20,
                headers={
                    'SOAPAction': 'http://tempuri.org/IConsultaCFDIService/Consulta',
                    'Content-Type': 'text/xml; charset=utf-8'
                })
            response = objectify.fromstring(soap_xml.text)
            status = response.xpath('//a:Estado', namespaces={
                'a': 'http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio'
            })
        except Exception as e:
            raise ValidationError(str(e))
        return CFDI_SAT_QR_STATE.get(status[0] if status else '', 'none')

    @api.depends('datas')
    def _compute_product_list(self):
        documents = self.filtered(
            lambda rec: rec.xunnel_document and rec.attachment_id)
        for rec in documents:
            xml = rec.get_xml_object(rec.datas)
            if xml is None:
                continue
            product_list = []
            for concepto in xml.Conceptos.iter(
                    '{http://www.sat.gob.mx/cfd/3}Concepto'):
                product_list += [concepto.get('Descripcion')]
            rec.product_list = json.dumps(product_list)

    def get_xml_object(self, xml):
        try:
            if isinstance(xml, bytes):
                xml = xml.decode()
            xml_str = base64.b64decode(xml.replace(
                'data:text/xml;base64,', ''))
            xml = objectify.fromstring(xml_str)
        except (AttributeError, SyntaxError):
            xml = False
        return xml

    @api.depends('datas')
    def _compute_related_cfdi(self):
        documents = self.filtered(lambda rec: rec.xunnel_document and rec.attachment_id)
        for rec in documents:
            xml = rec.get_xml_object(rec.datas)
            if xml is None:
                continue
            try:
                related_uuid = []
                for related in xml.CfdiRelacionados.iter('{http://www.sat.gob.mx/cfd/3}CfdiRelacionado'):
                    related_uuid += [related.get('UUID')]
                    rec.related_cfdi = json.dumps(related_uuid)
            except AttributeError:
                rec.related_cfdi = None
