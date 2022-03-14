import base64

from odoo.tests.common import TransactionCase

EMPTY_INVOICE = base64.b64encode(
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

INVOICE = base64.b64encode(
    bytes("""<?xml version="1.0" encoding="UTF-8"?>
    <SOAP-ENV:Envelope xmlns:ns0="http://tempuri.org/"
    xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
    <SOAP-ENV:Header/>
    <ns1:Body>
        <ns0:Consulta>
            <Comprobante
                Certificado="___ignore___"
                Fecha="2017-01-01T17:00:00"
                Folio="1"
                FormaPago="99"
                LugarExpedicion="85134"
                MetodoPago="PUE"
                Moneda="Gol"
                NoCertificado="''' + cls.certificate.serial_number + '''"
                Serie="INV/2017/01/"
                Sello="___ignore___"
                Descuento="2000.000"
                SubTotal="10000.000"
                Total="8480.000"
                TipoCambio="0.500000"
                TipoDeComprobante="I"
                Version="3.3">
                <Emisor
                    Rfc="EKU9003173C9"
                    Nombre="company_1_data"
                    RegimenFiscal="601"/>
                <Receptor
                    Rfc="XEXX010101000"
                    Nombre="partner_a"
                    UsoCFDI="P01"/>
                <Conceptos>
                    <Concepto
                        Cantidad="5.000000"
                        ClaveProdServ="01010101"
                        Descripcion="product_mx"
                        Importe="10000.000"
                        Descuento="2000.000"
                        ValorUnitario="2000.000">
                        <Impuestos>
                            <Traslados>
                                <Traslado
                                    Base="8000.000"
                                    Importe="1280.00"
                                    TasaOCuota="0.160000"
                                    TipoFactor="Tasa"/>
                            </Traslados>
                            <Retenciones>
                                <Retencion
                                    Base="8000.000"
                                    Importe="800.00"
                                    TasaOCuota="0.100000"
                                    TipoFactor="Tasa"/>
                            </Retenciones>
                        </Impuestos>
                    </Concepto>
                </Conceptos>
                <Impuestos
                    TotalImpuestosRetenidos="800.000"
                    TotalImpuestosTrasladados="1280.000">
                    <Retenciones>
                        <Retencion
                            Importe="800.000"/>
                    </Retenciones>
                    <Traslados>
                        <Traslado
                            Importe="1280.000"
                            TasaOCuota="0.160000"
                            TipoFactor="Tasa"/>
                    </Traslados>
                </Impuestos>
            </Comprobante>
            <ns0:expresionImpresa>${data}</ns0:expresionImpresa>
        </ns0:Consulta>
    </ns1:Body>
    </SOAP-ENV:Envelope>""", 'utf-8'))


class TestIrAttachment(TransactionCase):

    def setUp(self):
        super().setUp()
        self.attachment_obj = self.env['ir.attachment']
        self.attachment_1 = self.attachment_obj.create({
            'name': "an attachment",
            'datas': base64.b64encode(b'Invoice'),
        })
        self.attachment_2 = self.attachment_obj.create({
            'name': "an attachment",
            'datas': base64.b64encode(b'T'),
        })
        self.attachment_3 = self.attachment_obj.create({
            'name': "an empty invoice",
            'datas': EMPTY_INVOICE,
            'mimetype': 'application/xml',
        })
        self.attachment_4 = self.attachment_obj.create({
            'name': "an attachment",
            'datas': INVOICE,
        })

    def test_01_validate_xml(self):
        self.assertFalse(self.attachment_1._validate_xml(self.attachment_1.datas))
        self.assertFalse(self.attachment_2._validate_xml(self.attachment_2.datas))
        self.assertTrue(self.attachment_3._validate_xml(self.attachment_3.datas))

    def test_02_create_description(self):
        """ Case 1: A document with empty invoice is sent to _create_description, this should return an empty dict
            returned by the condition that's not met ´xml_obj.get('Version') != '3.3'´ on the method
        """
        res_1 = self.attachment_3._create_description(self.attachment_3.datas)
        self.assertEqual(res_1, {})

    def test_03_create(self):
        values = {
            'name': 'test attachment',
            'datas': EMPTY_INVOICE,
        }
        attachment = self.attachment_obj.create(values)
        self.assertFalse(attachment.description)

    def test_04_write(self):
        values = {
            'datas': base64.b64encode(b'Changed datas'),
        }
        self.assertNotEqual(self.attachment_3.datas, base64.b64encode(b'Changed datas'))
        self.attachment_3.write(values)
        self.assertEqual(self.attachment_3.datas, base64.b64encode(b'Changed datas'))
