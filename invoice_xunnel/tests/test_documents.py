import base64
import os

from odoo.tests.common import TransactionCase
from odoo.tools import misc
from requests_mock import mock

TEXT_xunnel_datas = base64.b64encode(
    bytes("""<?xml version="1.0" encoding="UTF-8"?>
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
    </SOAP-ENV:Envelope>""", 'utf-8'))

TEXT_datas = base64.b64encode(bytes("Test", 'utf-8'))

TEXT_xunnel_datas_invoice = base64.b64encode(
    bytes("""<?xml version="1.0" encoding="utf-8"?>
    <cfdi:Comprobante
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv33.xsd"
        LugarExpedicion="45116"
        MetodoPago="PUE"
        TipoDeComprobante="I"
        Total="666.66"
        Moneda="MXN"
        Certificado="test="
        Fecha="2021-11-02T11:25:54"
        Folio="666"
        Serie="F" Version="3.3" xmlns:cfdi="http://www.sat.gob.mx/cfd/3">
    <cfdi:Emisor Rfc="MXGODE561231GR8" Nombre="TEST EMISOR" RegimenFiscal="666">
    </cfdi:Emisor>
    <cfdi:Receptor Rfc="MXGODE561231GR8" Nombre="VAUXOO TEST" UsoCFDI="G03">
    </cfdi:Receptor>
    <cfdi:Conceptos>
        <cfdi:Concepto
            ClaveProdServ="80121666"
            Cantidad="1" ClaveUnidad="E666"
            Descripcion="IGUALA CORRESPONDIENTE AL MES DE NOVIEMBRE 2021"
            ValorUnitario="666.00"
            Importe="666.00">
                <cfdi:Impuestos>
                    <cfdi:Traslados>
                        <cfdi:Traslado Base="666.00"
                            Impuesto="002"
                            TipoFactor="Tasa"
                            TasaOCuota="0.160000"
                            Importe="3200.00"></cfdi:Traslado>
                    </cfdi:Traslados>
                </cfdi:Impuestos>
            </cfdi:Concepto>
        </cfdi:Conceptos>
        <cfdi:Impuestos TotalImpuestosTrasladados="3200.00">
            <cfdi:Traslados>
                <cfdi:Traslado Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="3200.00">
                </cfdi:Traslado>
            </cfdi:Traslados>
        </cfdi:Impuestos>
        <cfdi:Complemento>
            <tfd:TimbreFiscalDigital
                xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital"
                xsi:schemaLocation="http://www.sat.gob.mx/TimbreFiscalDigital
                http://www.sat.gob.mx/sitio_internet/cfd/TimbreFiscalDigital/TimbreFiscalDigitalv11.xsd"
                Version="1.1" UUID="648A7E33-DDDE-4522-AD82-8432A6455A58"
                FechaTimbrado="2021-11-02T11:27:39"
                RfcProvCertif="SAT970701NN3"
                SelloCFD="test="
                NoCertificadoSAT="000010000005666"
                SelloSAT="test=" />
            </cfdi:Complemento>
        </cfdi:Comprobante>""", 'utf-8'))


class TestCaseDocuments(TransactionCase):

    def setUp(self):
        super().setUp()
        self.url = "https://xunnel.com/"
        self.company = self.env['res.company'].browse(
            self.ref('base.main_company'))
        self.company.xunnel_token = 'test'
        self.company_id = self.company.id
        self.folder_a = self.env['documents.folder'].create({
            'name': 'folder A',
        })
        self.document = self.env['documents.document'].create({
            'datas': TEXT_datas,
            'name': 'file.txt',
            'mimetype': 'text/plain',
            'folder_id': self.folder_a.id,
            'xunnel_document': False,
        })
        self.document_xunnel = self.env['documents.document'].create({
            'datas': TEXT_xunnel_datas,
            'name': 'file.txt',
            'mimetype': 'text/plain',
            'folder_id': self.folder_a.id,
            'xunnel_document': True,
        })

    def test_01_compute_sat_status(self):
        """ Testing the result of calling _compute_sat_status() through 3 cases.
        Case 1: A document with xunnel_invoice = False and datas calls the method, the result is that the vaule of
            document.sat_status = none
        Case 2: A document with xunnel_document = True and datas = False calls the method, the result is that the
            value of document.sat_status = none"""
        self.document._compute_sat_status()
        self.assertEqual(self.document.sat_status, 'none')

        self.document.xunnel_document = True
        self.document.datas = False

    def test_02_get_xml_object(self):
        self.assertFalse(self.document.get_xml_object(self.document.datas))

        self.assertNotEqual(self.document_xunnel.get_xml_object(self.document_xunnel.datas), False)

    def test_03_open_documents(self):
        res = self.env['xunnel.documents.wizard'].open_documents()
        folder_id = self.env.ref('documents.documents_finance_folder')
        action = {
            'context': {
                'search_default_filter_downloaded_xml': True,
                'searchpanel_default_folder_id': folder_id.id,
                'downloaded_invoice': None,
                }
        }
        expected_res = action['context']
        self.assertEqual(res['context'], expected_res)

    @mock()
    def test_04_synchronize_documents(self, request=None):
        documents_response = misc.file_open(os.path.join('invoice_xunnel', 'tests', 'response_documents.json')).read()
        request.post('%sget_invoices_sat' % self.url, text=documents_response)
        doc = self.env['xunnel.documents.wizard'].create({})
        res = doc.synchronize_documents()
        created_document = self.env['documents.document'].search([], limit=1)
        action = {
            'context': {
                'default_message': '1 xml have been downloaded.',
                'default_no_attachment_action': False,
                'downloaded_invoice': [created_document.id],
                }
        }
        expected_res = action['context']
        self.assertEqual(res['context'], expected_res)

        error_response = misc.file_open(os.path.join('invoice_xunnel', 'tests', 'response_error.json')).read()
        request.post('%sget_invoices_sat' % self.url, text=error_response)
        res_error = doc.synchronize_documents()
        action = {
            'context': {
                'default_message': '0 xml have been downloaded. Also 18 files have failed at the conversion.',
                'default_no_attachment_action': True,
                'downloaded_invoice': [],
                }
        }
        expected_error_res = action['context']
        self.assertEqual(res_error['context'], expected_error_res)

    def test_05_compute_emitter_partner_id(self):
        self.attachment_obj = self.env['ir.attachment']
        attachment_1 = self.attachment_obj.create({
            'name': "an attachment",
            'datas': base64.b64encode(b'Invoice'),
            'description': 'a description emitter',
        })
        document_test = self.env['documents.document'].create({
            'datas': TEXT_xunnel_datas_invoice,
            'name': 'file.txt',
            'mimetype': 'text/plain',
            'folder_id': self.folder_a.id,
            'xunnel_document': True,
            'attachment_id': attachment_1.id,
        })
        partner = self.env['res.partner'].search([], limit=1)
        partner.vat = 'MXGODE561231GR8'
        document_test._compute_emitter_partner_id()
        self.assertEqual(document_test.emitter_partner_id, partner)
        self.assertEqual(document_test.invoice_total_amount, 666.66)

    def test_06_compute_related_cfdi(self):
        self.attachment_obj = self.env['ir.attachment']
        attachment_1 = self.attachment_obj.create({
            'name': "an attachment",
            'datas': base64.b64encode(b'Invoice'),
            'description': 'a description emitter',
        })
        document_test = self.env['documents.document'].create({
            'datas': TEXT_xunnel_datas_invoice,
            'name': 'file.txt',
            'mimetype': 'text/plain',
            'folder_id': self.folder_a.id,
            'xunnel_document': True,
            'attachment_id': attachment_1.id,
        })
        document_test._compute_related_cfdi()
        self.assertFalse(document_test.related_cfdi)
