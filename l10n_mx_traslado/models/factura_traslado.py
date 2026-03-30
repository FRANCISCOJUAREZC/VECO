# -*- coding: utf-8 -*-

import base64
import json
import requests
import datetime
import ast
from lxml import etree
import uuid
import random
import string
from odoo import fields, models, api,_
from odoo.exceptions import UserError
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm
from . import amount_to_text_es_MX
import pytz
from odoo import tools
import math
import re
import logging
_logger = logging.getLogger(__name__)

class CfdiTrasladoLine(models.Model):
    _name = "cfdi.traslado.line"
    _description = "CfdiTrasladoLine"

    cfdi_traslado_id= fields.Many2one(comodel_name='cfdi.traslado',string="CFDI Traslado")
    product_id = fields.Many2one('product.product',string='Producto',required=True)
    name = fields.Text(string='Descripción',required=True,)
    quantity = fields.Float(string='Cantidad', digits='Product Unit',required=True, default=1)
    price_unit = fields.Float(string='Precio unitario', required=True, digits='Product Price')
    invoice_line_tax_ids = fields.Many2many('account.tax',string='Taxes')
    currency_id = fields.Many2one('res.currency', related='cfdi_traslado_id.currency_id', store=True, related_sudo=False, readonly=False)
    price_subtotal = fields.Monetary(string='Subtotal',
        store=True, readonly=True, compute='_compute_price', help="Subtotal")
    price_total = fields.Monetary(string='Cantidad (con Impuestos)',
        store=True, readonly=True, compute='_compute_price', help="Cantidad total con impuestos")
    pesoenkg = fields.Float(string='Peso Kg', digits='Product Price')
    guias_line_ids = fields.Many2many('cfdi.guias.line', string='Guías', copy=True)
    aduanera_line_ids = fields.Many2many('cfdi.aduanera.line', string='Inf. Aduanera', copy=True)
    transporta_line_ids = fields.Many2many('cfdi.transporta.line', string='Cant. Trans.', copy=True)
    moneda = fields.Selection(
        selection=[('MXN', 'MXN'), 
                   ('USD', 'USD'), 
                   ('EUR', 'EUR'),
                   ('CAD', 'CAD')
                  ],
        string='Moneda',
        default = 'MXN'
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        self.name = self.product_id.partner_ref
        company_id = self.env.user.company_id
        taxes = self.product_id.taxes_id.filtered(lambda r: r.company_id == company_id)
        self.invoice_line_tax_ids = fp_taxes = taxes
        fix_price = self.env['account.tax']._fix_tax_included_price
        self.price_unit = fix_price(self.product_id.lst_price, taxes, fp_taxes)
        self.pesoenkg = self.product_id.weight

    @api.depends('price_unit', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'cfdi_traslado_id.partner_id', 'cfdi_traslado_id.currency_id',)
    def _compute_price(self):
        for line in self:
            currency = line.cfdi_traslado_id and line.cfdi_traslado_id.currency_id or None
            price = line.price_unit
            taxes = False
            if line.invoice_line_tax_ids:
                taxes = line.invoice_line_tax_ids.compute_all(price, currency, line.quantity, product=line.product_id, partner=line.cfdi_traslado_id.partner_id)
            line.price_subtotal = taxes['total_excluded'] if taxes else line.quantity * price
            line.price_total = taxes['total_included'] if taxes else line.price_subtotal

    @api.onchange('quantity')
    def _onchange_quantity(self):
        self.pesoenkg = self.product_id.weight * self.quantity

class CCPUbicacionesLine(models.Model):
    _name = "ccp.ubicaciones.line"
    _description = "CCPUbicacionesLine"
    
    cfdi_traslado_id= fields.Many2one(comodel_name='cfdi.traslado',string="CFDI Traslado")
    tipoubicacion = fields.Selection(
        selection=[('Origen', 'Origen'), 
                   ('Destino', 'Destino'),],
        string='Tipo Ubicación', required=True
    )
    contacto = fields.Many2one('res.partner',string="Remitente / Destinatario", required=True)
    numestacion = fields.Many2one('cve.estaciones',string='Número de estación')
    fecha = fields.Datetime(string='Fecha Salida / Llegada', required=True)
    tipoestacion = fields.Many2one('cve.estacion',string='Tipo estación')
    distanciarecorrida = fields.Float(string='Distancia recorrida')
    tipo_transporte = fields.Selection(
        selection=[('01', 'Autotransporte'), 
                  # ('02', 'Marítimo'), 
                   ('03', 'Aereo'),
                   #('04', 'Ferroviario')
                  ],
        string='Tipo de transporte'
    )
    idubicacion = fields.Char(string='ID Ubicacion')

class CCPRemolqueLine(models.Model):
    _name = "ccp.remolques.line"
    _description = "CCPRemolqueLine"

    cfdi_traslado_id= fields.Many2one(comodel_name='cfdi.traslado',string="CFDI Traslado")
    subtipo_id = fields.Many2one('cve.remolque.semiremolque',string="Subtipo")
    placa = fields.Char(string='Placa')

class CCPPropietariosLine(models.Model):
    _name = "ccp.figura.line"
    _description = "CCPPropietariosLine"

    cfdi_traslado_id= fields.Many2one(comodel_name='cfdi.traslado',string="CFDI Traslado")
    figura_id = fields.Many2one('res.partner',string="Contacto")
    tipofigura = fields.Many2one('cve.figura.transporte',string="Tipo figura")
    partetransporte = fields.Many2many('cve.parte.transporte',string="Parte transporte")

class CfdiAduaneraLine(models.Model):
    _name = "cfdi.aduanera.line"
    _description = "CCPaduaneraLine"
    _rec_name = "pedimento"

    cfdi_traslado_id= fields.Many2one(comodel_name='cfdi.traslado',string="CFDI Traslado")
    tipo_documento_id = fields.Many2one('ccp.tipo.documento',string='Tipo de documento',required=True)
    pedimento = fields.Text(string='Pedimento')
    id_doc_aduanero = fields.Text(string='Identificador documento aduanero')
    rfc_import = fields.Text(string='RFC de importador')

class CfdiTransportaLine(models.Model):
    _name = "cfdi.transporta.line"
    _description = "CCPTransportaLine"
    _rec_name = "name"

    cfdi_traslado_id= fields.Many2one(comodel_name='cfdi.traslado',string="CFDI Traslado")
    cantidad = fields.Float(string='Cantidad')
    idorigen = fields.Char(string='ID Origen')
    iddestino = fields.Char(string='ID Destino')
    name = fields.Char(string='Nombre')

class CfdiGuiasLine(models.Model):
    _name = "cfdi.guias.line"
    _description = "CCPguiasLine"
    _rec_name = "guiaid_numero"

    cfdi_traslado_id= fields.Many2one(comodel_name='cfdi.traslado',string="CFDI Traslado")
    guiaid_numero = fields.Char(string='No. Guia')
    guiaid_descrip = fields.Char(string='Descr. guia')
    guiaid_peso = fields.Float(string='Peso guia')

    @api.onchange('guiaid_numero')
    def _compute_no_guia(self):
        for rec in self:
            if rec.guiaid_numero:
                if len(rec.guiaid_numero) < 10:
                    raise UserError(_('El número de guia debe ser mayor de 10 y menor de 30 caracteres.'))

class CCPAduaneroLine(models.Model):
    _name = "ccp.aduanero.line"
    _description = "CCPAduaneroLine"

    cfdi_traslado_id= fields.Many2one(comodel_name='cfdi.traslado',string="CFDI Traslado")
    regimen_aduanero = fields.Many2one('ccp.regimen.aduanero',string='Regimen aduanero')

class CfdiTraslado(models.Model):
    _name = "cfdi.traslado"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "number"
    _description = "CfdiTraslado"

    factura_cfdi = fields.Boolean('Factura CFDI', copy=False)
    number = fields.Char(string="Numero", store=True, readonly=True, copy=False,
                         default=lambda self: _('Factura borrador'))
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('valid', 'Validada'),
        ('cancel', 'Cancelada'),
    ], string='Status', index=True, readonly=True, default='draft', )

    forma_pago = fields.Selection(
        selection=[('01', '01 - Efectivo'),
                   ('02', '02 - Cheque nominativo'),
                   ('03', '03 - Transferencia electrónica de fondos'),
                   ('04', '04 - Tarjeta de Crédito'),
                   ('05', '05 - Monedero electrónico'),
                   ('06', '06 - Dinero electrónico'),
                   ('08', '08 - Vales de despensa'),
                   ('12', '12 - Dación en pago'),
                   ('13', '13 - Pago por subrogación'),
                   ('14', '14 - Pago por consignación'),
                   ('15', '15 - Condonación'),
                   ('17', '17 - Compensación'),
                   ('23', '23 - Novación'),
                   ('24', '24 - Confusión'),
                   ('25', '25 - Remisión de deuda'),
                   ('26', '26 - Prescripción o caducidad'),
                   ('27', '27 - A satisfacción del acreedor'),
                   ('28', '28 - Tarjeta de débito'),
                   ('29', '29 - Tarjeta de servicios'),
                   ('30', '30 - Aplicación de anticipos'),
                   ('31', '31 - Intermediario pagos'),
                   ('99', '99 - Por definir'),],
        string='Forma de pago'
    )
    methodo_pago = fields.Selection(
        selection=[('PUE', 'Pago en una sola exhibición'),
                   ('PPD', 'Pago en parcialidades o diferido'),],
        string='Método de pago', 
    )
    uso_cfdi = fields.Selection(
        selection=[('G01', 'Adquisición de mercancías'),
                   ('G02', 'Devoluciones, descuentos o bonificaciones'),
                   ('G03', 'Gastos en general'),
                   ('I01', 'Construcciones'),
                   ('I02', 'Mobiliario y equipo de oficina por inversiones'),
                   ('I03', 'Equipo de transporte'),
                   ('I04', 'Equipo de cómputo y accesorios'),
                   ('I05', 'Dados, troqueles, moldes, matrices y herramental'),
                   ('I06', 'Comunicacion telefónica'),
                   ('I07', 'Comunicación Satelital'),
                   ('I08', 'Otra maquinaria y equipo'),
                   ('D01', 'Honorarios médicos, dentales y gastos hospitalarios'),
                   ('D02', 'Gastos médicos por incapacidad o discapacidad'),
                   ('D03', 'Gastos funerales'),
                   ('D04', 'Donativos'),
                   ('D05', 'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación).'),
                   ('D06', 'Aportaciones voluntarias al SAR.'),
                   ('D07', 'Primas por seguros de gastos médicos'),
                   ('D08', 'Gastos de transportación escolar obligatoria'),
                   ('D09', 'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones'),
                   ('D10', 'Pagos por servicios educativos (colegiaturas)'),
                   ('S01', 'Sin efectos fiscales'),
                   ('P01', 'Por definir (obsoleto)'),],
        string='Uso CFDI (cliente)',
        default = 'S01',
    )

    tipo_comprobante = fields.Selection(
        selection=[('I', 'Ingreso'),
                   ('E', 'Egreso'),
                   ('T', 'Traslado'),],
        string='Tipo de comprobante', default='T',
    )
    folio_fiscal = fields.Char('Folio Fiscal', readonly=True, copy=False)
    confirmacion = fields.Char('Confirmación')
    estado_factura = fields.Selection(
        selection=[('factura_no_generada', 'Factura no generada'), ('factura_correcta', 'Factura correcta'),
                   ('solicitud_cancelar', 'Cancelación en proceso'), ('factura_cancelada', 'Factura cancelada'),
                   ('solicitud_rechazada', 'Cancelación rechazada'), ],
        string='Estado de factura',
        default='factura_no_generada',
        readonly=True, copy=False
    )
    fecha_factura = fields.Datetime('Fecha Factura', copy=False)
    tipo_relacion = fields.Selection(
        selection=[('01', 'Nota de crédito de los documentos relacionados'),
                   ('02', 'Nota de débito de los documentos relacionados'),
                   ('03', 'Devolución de mercancía sobre facturas o traslados previos'),
                   ('04', 'Sustitución de los CFDI previos'),
                   ('05', 'Traslados de mercancías facturados previamente'),
                   ('06', 'Factura generada por los traslados previos'),
                   ('07', 'CFDI por aplicación de anticipo')],
        string='Tipo relación'
    )
    regimen_fiscal = fields.Selection(
        selection=[('601', 'General de Ley Personas Morales'),
                   ('603', 'Personas Morales con Fines no Lucrativos'),
                   ('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios'),
                   ('606', 'Arrendamiento'),
                   ('608', 'Demás ingresos'),
                   ('609', 'Consolidación'),
                   ('610', 'Residentes en el Extranjero sin Establecimiento Permanente en México'),
                   ('611', 'Ingresos por Dividendos (socios y accionistas)'),
                   ('612', 'Personas Físicas con Actividades Empresariales y Profesionales'),
                   ('614', 'Ingresos por intereses'),
                   ('616', 'Sin obligaciones fiscales'),
                   ('620', 'Sociedades Cooperativas de Producción que optan por diferir sus ingresos'),
                   ('621', 'Incorporación Fiscal'),
                   ('622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras'),
                   ('623', 'Opcional para Grupos de Sociedades'),
                   ('624', 'Coordinados'),
                   ('628', 'Hidrocarburos'),
                   ('607', 'Régimen de Enajenación o Adquisición de Bienes'),
                   ('629', 'De los Regímenes Fiscales Preferentes y de las Empresas Multinacionales'),
                   ('630', 'Enajenación de acciones en bolsa de valores'),
                   ('615', 'Régimen de los ingresos por obtención de premios'),
                   ('625', 'Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas'),
                   ('626', 'Régimen Simplificado de Confianza'),],
        string='Régimen Fiscal', 
    )
    uuid_relacionado = fields.Char(string='CFDI Relacionado')
    qr_value = fields.Char(string='QR Code Value', copy=False)
    qrcode_image = fields.Binary("QRCode", copy=False)
    comment = fields.Text("Comentario")
    partner_id = fields.Many2one('res.partner', string="Cliente", required=True, default=lambda self: self.env.company)
    source_document = fields.Char(string="Documento origen")
    invoice_date = fields.Datetime(string="Fecha de factura")
    factura_line_ids = fields.One2many('cfdi.traslado.line', 'cfdi_traslado_id', string='CFDI Traslado Line', copy=True)
    currency_id = fields.Many2one('res.currency',string='Moneda',default=lambda self: self.env.company.currency_id, required=True)
    amount_untaxed = fields.Float(string='Untaxed Amount', store=True, readonly=True, default=0)
    amount_tax = fields.Float(string='Tax', store=True, readonly=True, default=0)
    amount_total = fields.Float(string='Total', store=True, readonly=True, default=0)

    numero_cetificado = fields.Char(string='Numero de cetificado', copy=False)
    cetificaso_sat = fields.Char(string='Cetificao SAT', copy=False)
    fecha_certificacion = fields.Char(string='Fecha y Hora Certificación', copy=False)
    cadena_origenal = fields.Char(string='Cadena Origenal del Complemento digital de SAT', copy=False)
    selo_digital_cdfi = fields.Char(string='Selo Digital del CDFI', copy=False)
    selo_sat = fields.Char(string='Selo del SAT', copy=False)
    moneda = fields.Char(string='Moneda')
    tipocambio = fields.Char(string='TipoCambio')
    number_folio = fields.Char(string='Folio', compute='_get_number_folio')
    qr_value = fields.Char(string='QR Code Value')
    invoice_datetime = fields.Char(string='11/12/17 12:34:12')
    rfc_emisor = fields.Char(string='RFC')
    name_emisor = fields.Char(string='Name')
    serie_emisor = fields.Char(string='A')

    decimales = fields.Float(string='decimales')
    company_id = fields.Many2one('res.company', 'Compañia',
                                 default=lambda self: self.env.company)

    tipo_transporte = fields.Selection(
        selection=[('01', 'Autotransporte'), 
                  # ('02', 'Marítimo'), 
                   ('03', 'Aereo'),
                  # ('04', 'Ferroviario')
                  ],
        string='Tipo de transporte',required=True, default='01'
    )
    carta_porte = fields.Boolean('Agregar carta porte', default = True)

    ##### atributos CP 
    transpinternac = fields.Selection(
        selection=[('Sí', 'Si'), 
                   ('No', 'No'),],
        string='¿Es un transporte internacional?',default='No',
    )
    entradasalidamerc = fields.Selection(
        selection=[('Entrada', 'Entrada'), 
                   ('Salida', 'Salida'),],
        string='¿Las mercancías ingresan o salen del territorio nacional?',
    )
    viaentradasalida = fields.Many2one('cve.transporte',string='Vía de ingreso / salida')
    totaldistrec = fields.Float(string='Distancia recorrida')

    ##### ubicaciones CP
    ubicaciones_line_ids = fields.One2many('ccp.ubicaciones.line', 'cfdi_traslado_id', string='Ubicaciones', copy=True)

    ##### mercancias CP
    pesobrutototal = fields.Float(string='Peso bruto total', compute='_compute_pesobruto')
    unidadpeso = fields.Many2one('cve.clave.unidad',string='Unidad peso')
    pesonetototal = fields.Float(string='Peso neto total')
    numerototalmercancias = fields.Float(string='Numero total de mercancías', compute='_compute_mercancia')
    cargoportasacion = fields.Float(string='Cargo por tasación')

    #transporte
    permisosct = fields.Many2one('cve.tipo.permiso',string='Permiso SCT')
    numpermisosct = fields.Char(string='Número de permiso SCT')

    #autotransporte
    autotrasporte_ids = fields.Many2one('ccp.autotransporte',string='Unidad')
    remolque_line_ids = fields.One2many('ccp.remolques.line', 'cfdi_traslado_id', string='Remolque', copy=True)
    nombreaseg_merc = fields.Char(string='Nombre de la aseguradora')
    numpoliza_merc = fields.Char(string='Número de póliza')
    primaseguro_merc = fields.Float(string='Prima del seguro')
    seguro_ambiente = fields.Char(string='Nombre aseguradora')
    poliza_ambiente = fields.Char(string='Póliza no.')

    ##### Aereo CP
    numeroguia = fields.Char(string='Número de guía')
    lugarcontrato = fields.Char(string='Lugar de contrato')
    matriculaaeronave = fields.Char(string='Matrícula Aeronave')
    transportista_id = fields.Many2one('res.partner',string="Transportista")
    embarcador_id = fields.Many2one('res.partner',string="Embarcador")

    uuidcomercioext = fields.Char(string='UUID Comercio Exterior')
    paisorigendestino = fields.Many2one('res.country', string='País Origen / Destino')

    # figura transporte
    figuratransporte_ids = fields.One2many('ccp.figura.line', 'cfdi_traslado_id', string='Seguro mercancías', copy=True)
    IdCCP = fields.Char(string='IdCCP', readonly=True, copy=False)

    regimen_aduanero = fields.Many2one('ccp.regimen.aduanero',string='Regimen aduanero')
    aduanero_line_ids = fields.One2many('ccp.aduanero.line', 'cfdi_traslado_id', string='Regimen aduanero', copy=True)
#    RegistroISTMO = fields.Char(string=_('Registro ISTMO'))
#    UbicacionPoloOrigen = fields.Many2one('ccp.regimen.aduanero',string='Regimen aduanero')
#    UbicacionPoloDestino = fields.Many2one('ccp.regimen.aduanero',string='Regimen aduanero')
    LogisticaInversa = fields.Selection(
        selection=[('Sí', 'Si'),],
        string='Logistica Inversa Recoleccion Devolucion',
    )
    qr_ccp_value = fields.Char(string='QR CCP', copy=False)
    qrcode_ccp_image = fields.Binary("QRCode CCP", copy=False)
    aduanera_line_ids = fields.One2many('cfdi.aduanera.line', 'cfdi_traslado_id', string='CFDI Aduanera Line', copy=True)
    guias_line_ids = fields.One2many('cfdi.guias.line', 'cfdi_traslado_id', string='CFDI Guias Line', copy=True)
    manejodeguias = fields.Boolean('Manejo de guías')
    transporta_line_ids = fields.One2many('cfdi.transporta.line', 'cfdi_traslado_id', string='CFDI Transporte Line', copy=True)
    manejodeids = fields.Boolean('Manejo de IDs')

    @api.depends('number')
    def _get_number_folio(self):
        if self.number:
            self.number_folio = self.number.replace('CT','').replace('/','')

    @api.model
    def _get_amount_2_text(self, amount_total):
        return amount_to_text_es_MX.get_amount_to_text(self, amount_total, 'es_cheque', self.currency_id.name)

    @api.model
    def _default_journal(self):
        if not self.journal_id:
            company_id = self._context.get('default_company_id', self.env.company.id)
            return self.env['account.journal'].search([('type','=','sale'),('company_id', '=', company_id)],limit=1)

    journal_id = fields.Many2one('account.journal', 'Diario', default=_default_journal)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', _('Draft Invoice')) == _('Draft Invoice'):
                if 'company_id' in vals:
                    vals['number'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('cfdi.traslado') or _('Draft Invoice')
                else:
                    vals['number'] = self.env['ir.sequence'].next_by_code('cfdi.traslado') or _('Draft Invoice')
        result = super(CfdiTraslado, self).create(vals)
        return result

    def action_valid(self):
        self.write({'state': 'valid'})
        self.invoice_date = datetime.datetime.now()

    def action_set_draft(self):
        self.write({'state':'draft'})
        
    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('factura_line_ids')
    def _compute_pesobruto(self):
        peso = 0
        for rec in self:
           if rec.factura_line_ids:
               for line in rec.factura_line_ids:
                 peso += line.pesoenkg
           rec.pesobrutototal = peso

    @api.onchange('factura_line_ids')
    def _compute_pesoneto(self):
        peso = 0
        for rec in self:
           if rec.factura_line_ids:
               for line in rec.factura_line_ids:
                  peso += line.pesoenkg
           rec.pesonetototal = peso

    @api.onchange('factura_line_ids')
    def _compute_mercancia(self):
        cant = 0
        for rec in self:
            if rec.factura_line_ids:
                for line in rec.factura_line_ids:
                    cant += 1
            rec.numerototalmercancias = cant

    @api.model
    def to_json(self):
        #if self.partner_id.vat == 'XAXX010101000':
        #    nombre = 'PUBLICO EN GENERAL'
        #else:

        no_decimales = 2
        no_decimales_prod = 2
        no_decimales_tc = 2

        self.check_cfdi_values()

        root_company = self.company_id.sudo().parent_ids[::-1].filtered('l10n_mx_edi_certificate_ids')[:1]
        if root_company.l10n_mx_edi_pac:
            pac_test_env = root_company.l10n_mx_edi_pac_test_env
            pac_password = root_company.sudo().l10n_mx_edi_pac_password
            if not pac_test_env and not pac_password:
                raise UserError(_("Falta aregar credenciales al PAC"))
        else:
            raise UserError(_("Falta especificar el PAC"))

        certificate_sudo = root_company.sudo().l10n_mx_edi_certificate_ids.filtered('is_valid')[:1]

        if not certificate_sudo:
            raise UserError(_("No se encontró un certificado válido"))

        #corregir hora
        timezone = self._context.get('tz')
        if not timezone:
            timezone = self.journal_id.tz or self.env.user.partner_id.tz or 'America/Mexico_City'
        # timezone = tools.ustr(timezone).encode('utf-8')

        local = pytz.timezone(timezone)
        if not self.fecha_factura:
           naive_from = datetime.datetime.now()
        else:
           naive_from = self.fecha_factura
        local_dt_from = naive_from.replace(tzinfo=pytz.UTC).astimezone(local)
        date_from = local_dt_from.strftime ("%Y-%m-%dT%H:%M:%S")
        if not self.fecha_factura:
           self.fecha_factura = datetime.datetime.now()

        request_params = {
                'certificate': certificate_sudo,
                'factura': {
                      'serie': str(re.sub(r'[0-9]+', '', self.number)).replace('/', ''),
                      'folio': str(re.sub('[^0-9]','', self.number)),
                      'fecha_expedicion': date_from,
                     # 'forma_pago':'',
                      'subtotal': self.amount_untaxed,
                     # 'descuento': 0,
                      'moneda': 'XXX',
                     # 'tipocambio': tipocambio,
                      'total': self.amount_total,
                      'tipocomprobante': self.tipo_comprobante,
                      'metodo_pago': self.methodo_pago,
                      'LugarExpedicion': self.company_id.zip,
                      'Confirmacion': self.confirmacion,
                      'Exportacion': '01',
                      'no_certificado': ('%x' % int(certificate_sudo.serial_number))[1::2],
                      'certificado': certificate_sudo._get_der_certificate_bytes(formatting='base64').decode(),
                },
                'emisor': {
                      'rfc': self.company_id.vat.upper(),
                      'nombre': self.clean_text(self.company_id.name).upper(),
                      'RegimenFiscal': self.company_id.l10n_mx_edi_fiscal_regime,
                },
                'receptor': {
                      'nombre': self.clean_text(self.company_id.name).upper(),
                      'rfc': self.company_id.vat.upper() if self.company_id.partner_id.country_id.l10n_mx_edi_code == 'MEX' else None,
                      'ResidenciaFiscal': self.company_id.partner_id.country_id.l10n_mx_edi_code if self.company_id.partner_id.country_id.l10n_mx_edi_code != 'MEX' else None,
                      'NumRegIdTrib': self.company_id.vat.upper() if self.company_id.partner_id.country_id.l10n_mx_edi_code != 'MEX' else None,
                      'UsoCFDI': self.uso_cfdi,
                      'RegimenFiscalReceptor': self.company_id.l10n_mx_edi_fiscal_regime,
                      'DomicilioFiscalReceptor': self.company_id.zip,
                },
                'informacion': {
                      'cfdi': '4.0',
                      'sistema': 'odoo19 EE',
                      'version': '2',
                },
        }

        if self.uuid_relacionado:
            cfdi_relacionado = []
            uuids = self.uuid_relacionado.replace(' ', '').split(',')
            for uuid in uuids:
                cfdi_relacionado.append({
                    'uuid': uuid.upper(),
                })
            request_params.update({'CfdisRelacionados': {'UUID': cfdi_relacionado, 'TipoRelacion': self.tipo_relacion}})

        items = {'numerodepartidas': len(self.factura_line_ids)}
        invoice_lines = []
        for line in self.factura_line_ids:
                invoice_lines.append({'cantidad': self.set_decimals(line.quantity,6),
                                      'unidad': line.product_id.uom_id.name,
                                      'NoIdentificacion': line.product_id.default_code,
                                      'valorunitario': self.set_decimals(line.price_unit, no_decimales_prod),
                                      'importe': self.set_decimals(line.price_unit * line.quantity, no_decimales_prod),
                                      'descripcion': self.clean_text(line.product_id.name),
                                      'ClaveProdServ': line.product_id.unspsc_code_id.code,
                                      'ObjetoImp': '01',
                                      'ClaveUnidad': line.product_id.uom_id.unspsc_code_id.code})

        request_params['factura'].update({'subtotal': '0','total': '0'})

        request_params.update({'conceptos': invoice_lines})

#        if not self.company_id.archivo_cer:
#            raise UserError(_('Archivo .cer path is missing.'))
#        if not self.company_id.archivo_key:
#            raise UserError(_('Archivo .key path is missing.'))
#        archivo_cer = self.company_id.archivo_cer
#        archivo_key = self.company_id.archivo_key
#        request_params.update({
#            'certificados': {
#                'archivo_cer': archivo_cer.decode("utf-8"),
#                'archivo_key': archivo_key.decode("utf-8"),
#                'contrasena': self.company_id.contrasena,
#            }})
        return request_params

    def set_decimals(self, amount, precision):
        if amount is None or amount is False:
            return None
        return '%.*f' % (precision, amount)

    def clean_text(self, text):
        clean_text = text.replace('\n', ' ').replace('\\', ' ').replace('-', ' ').replace('/', ' ').replace('|', ' ')
        clean_text = clean_text.replace(',', ' ').replace(';', ' ').replace('>', ' ').replace('<', ' ')
        return clean_text[:1000]

    def check_cfdi_values(self):
        if not self.company_id.vat:
            raise UserError(_('El emisor no tiene RFC configurado.'))
        if not self.company_id.name:
            raise UserError(_('El emisor no tiene nombre configurado.'))
        if not self.company_id.l10n_mx_edi_fiscal_regime:
            raise UserError(_('El emisor no régimen fiscal configurado.'))

    def _set_data_from_xml(self, xml_invoice):
        if not xml_invoice:
            return None
        NSMAP = {
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        }

        xml_data = etree.fromstring(xml_invoice)
        Complemento = xml_data.find('cfdi:Complemento', NSMAP)
        TimbreFiscalDigital = Complemento.find('tfd:TimbreFiscalDigital', NSMAP)

        self.moneda = xml_data.attrib['Moneda']
        self.numero_cetificado = xml_data.attrib['NoCertificado']
        self.cetificaso_sat = TimbreFiscalDigital.attrib['NoCertificadoSAT']
        self.fecha_certificacion = TimbreFiscalDigital.attrib['FechaTimbrado']
        self.selo_digital_cdfi = TimbreFiscalDigital.attrib['SelloCFD']
        self.selo_sat = TimbreFiscalDigital.attrib['SelloSAT']
        self.folio_fiscal = TimbreFiscalDigital.attrib['UUID']
        self.invoice_datetime = xml_data.attrib['Fecha']
#        if not self.fecha_factura:
#            self.fecha_factura = self.invoice_datetime.replace('T', ' ')
        version = TimbreFiscalDigital.attrib['Version']
        self.cadena_origenal = '||%s|%s|%s|%s|%s||' % (version, self.folio_fiscal, self.fecha_certificacion,
                                                       self.selo_digital_cdfi, self.cetificaso_sat)

        options = {'width': 275 * mm, 'height': 275 * mm}
        amount_str = str(self.amount_total).split('.')
        qr_value = 'https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id=%s&re=%s&rr=%s&tt=%s.%s&fe=%s' % (
            self.folio_fiscal,
            self.company_id.vat,
            self.company_id.vat,
            amount_str[0].zfill(10),
            amount_str[1].ljust(6, '0'),
            self.selo_digital_cdfi[-8:],
        )
        self.qr_value = qr_value
        ret_val = createBarcodeDrawing('QR', value=qr_value, **options)
        self.qrcode_image = base64.encodebytes(ret_val.asString('jpg'))

        ubicacion = self.ubicaciones_line_ids[0]
        #corregir hora
        timezone = self._context.get('tz')
        if not timezone:
           timezone = self.journal_id.tz or self.env.user.partner_id.tz or 'America/Mexico_City'
        local = pytz.timezone(timezone)
        local_dt_from = ubicacion.fecha.replace(tzinfo=pytz.UTC).astimezone(local)
        fechaorig = local_dt_from.strftime ("%Y-%m-%dT%H:%M:%S")
        qr_ccp_value = 'https://verificacfdi.facturaelectronica.sat.gob.mx/verificaccp/default.aspx?IdCCP=%s&FechaOrig=%s&FechaTimb=%s' % (
            self.IdCCP,
            fechaorig,
            self.fecha_certificacion,
        )
        self.qr_ccp_value = qr_ccp_value
        ret_val = createBarcodeDrawing('QR', value=qr_ccp_value, **options)
        self.qrcode_ccp_image = base64.encodebytes(ret_val.asString('jpg'))

    ################################################################################################################
    ###############################  Adicional de Complemento de traslado ##########################################
    ################################################################################################################
    @api.model
    def to_json_carta_porte(self, request_params):
        res =  request_params
        self.totaldistrec = 0

        if not self.IdCCP:
           self.IdCCP = str(uuid.uuid4()).upper()
           self.IdCCP = self.IdCCP[:0] + 'CCC' + self.IdCCP[3:]

        cp_ubicacion = []
        for ubicacion in self.ubicaciones_line_ids:

            #corregir hora
            timezone = self._context.get('tz')
            if not timezone:
               timezone = self.journal_id.tz or self.env.user.partner_id.tz or 'America/Mexico_City'
            local = pytz.timezone(timezone)
            local_dt_from = ubicacion.fecha.replace(tzinfo=pytz.UTC).astimezone(local)
            date_fecha = local_dt_from.strftime ("%Y-%m-%dT%H:%M:%S")
            self.totaldistrec += float(ubicacion.distanciarecorrida)
            #_logger.info('totaldistrec %s', self.totaldistrec)

            cp_ubicacion.append({
                            'TipoUbicacion': ubicacion.tipoubicacion,
                            'IDUbicacion': ubicacion.idubicacion,
                            'RFCRemitenteDestinatario': ubicacion.contacto.vat if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else '',
                            'NombreRemitenteDestinatario': ubicacion.contacto.name,
                            'NumRegIdTrib': ubicacion.contacto.vat if ubicacion.contacto.country_id.l10n_mx_edi_code != 'MEX' else '',
                            'ResidenciaFiscal': ubicacion.contacto.country_id.l10n_mx_edi_code if ubicacion.contacto.country_id.l10n_mx_edi_code != 'MEX' else '',
                            'NumEstacion': self.tipo_transporte != '01' and ubicacion.numestacion.clave_identificacion or '',
                            'NombreEstacion': self.tipo_transporte != '01' and ubicacion.numestacion.descripcion or '',
                          # 'NavegacionTrafico': self.company_id.zip,
                            'FechaHoraSalidaLlegada': date_fecha,
                            'TipoEstacion': self.tipo_transporte != '01' and ubicacion.tipoestacion.c_estacion or '',
                            'DistanciaRecorrida': ubicacion.distanciarecorrida > 0 and ubicacion.distanciarecorrida or '',
                            'Domicilio': {
                                'Calle': ubicacion.contacto.street_name,
                                'NumeroExterior': ubicacion.contacto.street_number,
                                'NumeroInterior': ubicacion.contacto.street_number2,
                                'Colonia': ubicacion.contacto.l10n_mx_edi_colony_code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.l10n_mx_edi_colony or None,
                                'Localidad': ubicacion.contacto.l10n_mx_edi_locality_id.code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.l10n_mx_edi_locality,
                          #      'Referencia': self.company_id.cce_clave_estado.c_estado,
                                'Municipio': ubicacion.contacto.city_id.l10n_mx_edi_code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.city,
                                'Estado': ubicacion.contacto.state_id.code if ubicacion.contacto.country_id.l10n_mx_edi_code in ('MEX', 'USA', 'CAN') or ubicacion.contacto.state_id.code else 'NA',
                                'Pais': ubicacion.contacto.country_id.l10n_mx_edi_code,
                                'CodigoPostal': ubicacion.contacto.zip,
                            },
                         })

        #################  Atributos y Ubicacion ############################
   #     if self.tipo_transporte == '01' or self.tipo_transporte == '04':
        cartaporte31= {
                       'IdCCP': self.IdCCP,
                       'TranspInternac': self.transpinternac,
                     #  'RegimenAduanero': self.regimen_aduanero.clave,
                       'EntradaSalidaMerc': self.entradasalidamerc,
                       'ViaEntradaSalida': self.viaentradasalida.c_transporte,
                       'TotalDistRec': self.tipo_transporte == '01' and self.totaldistrec or '',
                       'PaisOrigenDestino': self.paisorigendestino.l10n_mx_edi_code,
                      }

        if self.aduanero_line_ids:
           cp_aduanero = []
           for aduanero in self.aduanero_line_ids:
               cp_aduanero.append({
                               'RegimenAduanero': aduanero.regimen_aduanero.clave,
                            })
           cartaporte31.update({'Aduaneros': cp_aduanero})

        cartaporte31.update({'Ubicaciones': cp_ubicacion})

        #################  Mercancias ############################
        mercancias = { 
                       'PesoBrutoTotal': self.pesobrutototal, #solo si es aereo o ferroviario
                       'UnidadPeso': self.unidadpeso.clave,
                       'PesoNetoTotal': self.pesonetototal if self.pesonetototal > 0 else '',
                       'NumTotalMercancias': int(self.numerototalmercancias),
                       'CargoPorTasacion': self.cargoportasacion if self.cargoportasacion > 0 else '',
                       'LogisticaInversa': self.LogisticaInversa,
        }

        mercancia = []
        mercancia_atributos = []
        for line in self.factura_line_ids:
            if line.quantity <= 0:
                continue

            #################  Guias ############################
            guias = []
            for guia_line in line.guias_line_ids:
                guias.append({
                          'NumeroGuiaIdentificacion': guia_line.guiaid_numero,
                          'DescripGuiaIdentificacion': guia_line.guiaid_descrip,
                          'PesoGuiaIdentificacion': guia_line.guiaid_peso,
                })

            #################  Pedimentos ############################
            pedimentos = []
            for aduanera_line in line.aduanera_line_ids:
                pedimentos.append({
                          'TipoDocumento': aduanera_line.tipo_documento_id.clave,
                          'NumPedimento': aduanera_line.pedimento[:2] + '  ' + aduanera_line.pedimento[2:4] + '  ' + aduanera_line.pedimento[4:8] + '  ' + aduanera_line.pedimento[8:],
                          'IdentDocAduanero': aduanera_line.id_doc_aduanero,
                          'RFCImpo': aduanera_line.rfc_import,
                })

            #################  CantidadTransporta ############################
            transporta = []
            for transporta_line in line.transporta_line_ids:
                transporta.append({
                                'Cantidad': transporta_line.cantidad,
                                'IDOrigen': transporta_line.idorigen,
                                'IDDestino': transporta_line.iddestino,
                                #'CvesTransporte': merc.valorunitarioaduana,
                })

            #################  DetalleMercancia ############################
      #      mercancia_detalle = {
      #                          'UnidadPesoMerc': merc.product_id.code,
      #                          'PesoBruto': merc.fraccionarancelaria.c_fraccionarancelaria,
      #                          'PesoNeto': merc.cantidadaduana,
      #                          'PesoTara': merc.valorunitarioaduana,
      #                          'NumPiezas': merc.valordolares,
      #      }

            mercancia_atributos.append({
                            'BienesTransp': line.product_id.unspsc_code_id.code,
                            'ClaveSTCC': line.product_id.clave_stcc,
                            'Descripcion': self.clean_text(line.product_id.name),
                            'Cantidad': line.quantity,
                            'ClaveUnidad': line.product_id.uom_id.unspsc_code_id.code,
                            'Unidad': line.product_id.uom_id.name,
                            'Dimensiones': line.product_id.dimensiones,
                            'MaterialPeligroso': line.product_id.materialpeligroso,
                            'CveMaterialPeligroso': line.product_id.clavematpeligroso.clave,
                            'Embalaje': line.product_id.embalaje and line.product_id.embalaje.clave or '',
                            'DescripEmbalaje': line.product_id.desc_embalaje and line.product_id.desc_embalaje or '',
                            'PesoEnKg': line.pesoenkg,
                            'ValorMercancia': line.price_subtotal,
                            'Moneda': line.moneda,
                            'FraccionArancelaria': line.product_id.l10n_mx_edi_tariff_fraction_id.code if self.transpinternac == 'Sí' else '',
                            'UUIDComercioExt': self.uuidcomercioext,
                            'SectorCofepris': line.product_id.SectorCofepris.clave,
                            'IngredienteActivo': line.product_id.IngredienteActivo,
                            'NomQuimico': line.product_id.NomQuimico,
                            'DenominacionGenerica': line.product_id.DenominacionGenerica,
                            'DenominacionDistintiva': line.product_id.DenominacionDistintiva,
                            'Fabricante': line.product_id.Fabricante,
                            'FechaCaducidad': line.product_id.FechaCaducidad,
                            'LoteMedicamento': line.product_id.LoteMedicamento,
                            'FormaFarmaceutica': line.product_id.FormaFarmaceutica.clave,
                            'CondicionesEsp': line.product_id.CondicionesEsp.clave,
                            'RegistroSanitario': line.product_id.RegistroSanitario,
                            'PermisoImportacion': line.product_id.PermisoImportacion,
                            'FolioImpoVUCEM': line.product_id.FolioImpoVUCEM,
                            'NumCAS': line.product_id.NumCAS,
                            'RazonSocialEmpImp': line.product_id.RazonSocialEmpImp,
                            'NumRegSan': line.product_id.NumRegSan,
                            'DatosFabricante': line.product_id.DatosFabricante,
                            'DatosFormulador': line.product_id.DatosFormulador,
                            'DatosMaquilador': line.product_id.DatosMaquilador,
                            'UsoAutorizado': line.product_id.UsoAutorizado,
                            'TipoMateria': line.product_id.TipoMateria.clave,
                            'DescripcionMateria': line.product_id.DescripcionMateria,
                            'GuiasIdentificacion': guias,
                            'DocumentacionAduanera': pedimentos,
                            'CantidadTransporta': transporta,
            })
        mercancias.update({'mercancia': {'atributos': mercancia_atributos}})

        if self.tipo_transporte == '01': #autotransporte
              transpote_detalle = {
                            'PermSCT': self.permisosct.clave,
                            'NumPermisoSCT': self.numpermisosct,
                            'IdentificacionVehicular': {
                                 'ConfigVehicular': self.autotrasporte_ids.confvehicular.clave,
                                 'PesoBrutoVehicular': self.autotrasporte_ids.PesoBrutoVehicular,
                                 'PlacaVM': self.autotrasporte_ids.placavm,
                                 'AnioModeloVM': self.autotrasporte_ids.aniomodelo,
                            },
                            'Seguros': {
                                 'AseguraRespCivil': self.autotrasporte_ids.nombreaseg,
                                 'PolizaRespCivil': self.autotrasporte_ids.numpoliza,
                                 'AseguraCarga': self.nombreaseg_merc,
                                 'PolizaCarga': self.numpoliza_merc,
                                 'PrimaSeguro': self.primaseguro_merc or None,
                                 'AseguraMedAmbiente': self.seguro_ambiente or None,
                                 'PolizaMedAmbiente': self.poliza_ambiente or None,
                            },
              }
              remolques = []
              if self.remolque_line_ids:
                 for remolque in self.remolque_line_ids:
                     remolques.append({
                            'SubTipoRem': remolque.subtipo_id.clave,
                            'Placa': remolque.placa,
                     })
                 transpote_detalle.update({'Remolques': remolques})

              mercancias.update({'Autotransporte': transpote_detalle})
        elif self.tipo_transporte == '02': # maritimo
              maritimo = []
        elif self.tipo_transporte == '03': #aereo
              transpote_detalle = {
                            'PermSCT': self.permisosct.clave,
                            'NumPermisoSCT': self.numpermisosct,
                            'MatriculaAeronave': self.matriculaaeronave,
                         #   'NombreAseg': self.nombreaseg,  ******
                         #   'NumPolizaSeguro': self.numpoliza, *****
                            'NumeroGuia': self.numeroguia,
                            'LugarContrato': self.lugarcontrato,
                            'CodigoTransportista': self.transportista_id.codigotransportista.clave,
                            'RFCEmbarcador': self.embarcador_id.vat if self.embarcador_id.country_id.l10n_mx_edi_code != 'MEX' else '',
                            'NumRegIdTribEmbarc': self.embarcador_id.registro_tributario,
                            'ResidenciaFiscalEmbarc': self.embarcador_id.country_id.l10n_mx_edi_code if self.embarcador_id.country_id.l10n_mx_edi_code != 'MEX' else '',
                            'NombreEmbarcador': self.embarcador_id.name,
              }
              mercancias.update({'TransporteAereo': transpote_detalle})
        elif self.tipo_transporte == '04': #ferroviario
              ferroviario = []

        cartaporte31.update({'Mercancias': mercancias})

        #################  Figura transporte ############################
        figuratransporte = []
        tipos_figura = []
        for figura in self.figuratransporte_ids:
            tipos_figura = {
                       'TipoFigura': figura.tipofigura.clave,
                       'RFCFigura': figura.figura_id.vat if figura.figura_id.country_id.l10n_mx_edi_code == 'MEX' else '',
                       'NumLicencia': figura.figura_id.cce_licencia,
                       'NombreFigura': figura.figura_id.name,
                       'NumRegIdTribFigura': figura.figura_id.vat if figura.figura_id.country_id.l10n_mx_edi_code != 'MEX' else '',
                       'ResidenciaFiscalFigura': figura.figura_id.country_id.l10n_mx_edi_code if figura.figura_id.country_id.l10n_mx_edi_code != 'MEX' else '',
                       'Domicilio': {
                                'Calle': figura.figura_id.street_name,
                                'NumeroExterior': figura.figura_id.street_number,
                                'NumeroInterior': figura.figura_id.street_number2,
                                'Colonia': figura.figura_id.l10n_mx_edi_colony_code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.l10n_mx_edi_colony or None,
                                'Localidad': figura.figura_id.l10n_mx_edi_locality_id.code if ubicacion.contacto.country_id.l10n_mx_edi_code == 'MEX' else ubicacion.contacto.l10n_mx_edi_locality,
                          #      'Referencia': operador.company_id.cce_clave_estado.c_estado,
                                'Municipio': figura.figura_id.city_id.l10n_mx_edi_code if figura.figura_id.country_id.l10n_mx_edi_code == 'MEX' else figura.figura_id.city,
                                'Estado': figura.figura_id.state_id.code if figura.figura_id.country_id.l10n_mx_edi_code in ('MEX', 'USA', 'CAN') or figura.figura_id.state_id.code else 'NA',
                                'Pais': figura.figura_id.country_id.l10n_mx_edi_code,
                                'CodigoPostal': figura.figura_id.zip,
                       },
            }

            partes = []
            for parte in figura.partetransporte:
               partes.append({
                    'ParteTransporte': parte.clave,
               })
            figuratransporte.append({'TiposFigura': tipos_figura, 'PartesTransporte': partes})

        cartaporte31.update({'FiguraTransporte': figuratransporte})
        res.update({'cartaporte31': cartaporte31})

        return res

    def _get_cadena_xslts(self):
        return 'l10n_mx_edi/data/4.0/xslt/cadenaoriginal_TFD.xslt', 'l10n_mx_edi/data/4.0/xslt/cadenaoriginal.xslt'

    @api.model
    def _decode_cfdi_attachment(self, cfdi_data):
        """ Extract relevant data from the CFDI attachment.

        :param: cfdi_data:      The cfdi data as raw bytes.
        :return:                A python dictionary.
        """
        cadena_tfd, cadena = self._get_cadena_xslts()

        def get_cadena(cfdi_node, template):
            if cfdi_node is None:
                return None
            with tools.file_open(template) as f:
                cadena_root = etree.parse(f)
                return str(etree.XSLT(cadena_root)(cfdi_node))

        def get_node(node, xpath):
            nodes = node.xpath(xpath)
            return nodes[0] if nodes else None

        def get_value(node, key):
            if node is None:
                return None
            upper_key = key[0].upper() + key[1:]
            lower_key = key[0].lower() + key[1:]
            return node.get(upper_key) or node.get(lower_key)

        # Nothing to decode.
        if not cfdi_data:
            return {}

        try:
            cfdi_node = etree.fromstring(cfdi_data)
            emisor_node = get_node(cfdi_node, "//*[local-name()='Emisor']")
            receptor_node = get_node(cfdi_node, "//*[local-name()='Receptor']")
            info_global_node = get_node(cfdi_node, "//*[local-name()='InformacionGlobal']")
            relacionado_nodes = cfdi_node.xpath("//*[local-name()='CfdiRelacionados']")
        except etree.XMLSyntaxError:
            # Not an xml
            return {}
        except AttributeError:
            # Not a CFDI
            return {}

        tfd_node = get_node(cfdi_node, "//*[local-name()='TimbreFiscalDigital']")
        origin = None
        origin_list = []
        cfdi_relation_data = []
        for node in relacionado_nodes:
            origin_type = get_value(node, "TipoRelacion")
            uuid_nodes = node.getchildren()
            origin_uuids = []
            for uuid_node in uuid_nodes:
                if uuid := get_value(uuid_node, 'UUID'):
                    origin_uuids.append(uuid)
                    cfdi_relation_data.append({'relation_type': origin_type, 'uuid': uuid})
            if origin_uuids and origin_type:
                origin_uuids_str = ','.join(origin_uuids)
                origin_list.append(f'{origin_type}|{origin_uuids_str}')

        if origin_list:
            origin = ','.join(origin_list)

        return {
            'uuid': get_value(tfd_node, 'UUID'),
            'supplier_rfc': get_value(emisor_node, 'Rfc'),
            'customer_rfc': get_value(receptor_node, 'Rfc'),
            'amount_total': get_value(cfdi_node, 'Total'),
            'cfdi_node': cfdi_node,
            'usage': get_value(receptor_node, 'UsoCFDI'),
            'payment_method': get_value(cfdi_node, 'formaDePago') or get_value(cfdi_node, 'MetodoPago'),
            'bank_account': get_value(cfdi_node, 'NumCtaPago'),
            'sello': get_value(cfdi_node, 'sello') or 'No identificado',
            'sello_sat': get_value(tfd_node, 'SelloSAT') or 'No identificado',
            'cadena': get_cadena(tfd_node, cadena_tfd) or get_cadena(cfdi_node, cadena),
            'certificate_number': get_value(cfdi_node, 'NoCertificado'),
            'certificate_sat_number': get_value(tfd_node, 'NoCertificadoSAT'),
            'expedition': get_value(cfdi_node, 'LugarExpedicion'),
            'fiscal_regime': get_value(emisor_node, 'RegimenFiscal') or '',
            'emission_date_str': (get_value(cfdi_node, 'Fecha') or '').replace('T', ' '),
            'stamp_date': (get_value(tfd_node, 'FechaTimbrado') or '').replace('T', ' '),
            'periodicity': get_value(info_global_node, 'Periodicidad'),
            'origin': origin,
            'cfdi_relation_data': cfdi_relation_data
        }

    def _l10n_mx_edi_get_invoice_templates(self):
        return 'l10n_mx_traslado.cfdi_traslado', 'l10n_mx_edi_40/data/4.0/xslt/cadenaoriginal_TFD.xslt'

    def action_cfdi_generate(self):
        for invoice in self:
            if invoice.estado_factura == 'factura_correcta':
                if invoice.folio_fiscal:
                    invoice.write({'factura_cfdi': True})
                    return True
                else:
                    raise UserError(_('Error para timbrar factura, Factura ya generada.'))
            if invoice.estado_factura == 'factura_cancelada':
                raise UserError(_('Error para timbrar factura, Factura ya generada y cancelada.'))

            # == CFDI values ==
            cfdi_values = invoice.to_json()
            if invoice.carta_porte:
                 cfdi_values = invoice.to_json_carta_porte(cfdi_values)
            #_logger.info('json %s', cfdi_values)
            qweb_template, xsd_attachment_name = invoice._l10n_mx_edi_get_invoice_templates()

            # == Generate the CFDI ==
            cfdi = self.env['ir.qweb']._render(qweb_template, cfdi_values)
            #_logger.info('cfdi %s', cfdi)
            decoded_cfdi_values = invoice._decode_cfdi_attachment(cfdi_data=cfdi)
            #cfdi_cadena_crypted = cfdi_values['certificate'].sudo()._get_encrypted_cadena(decoded_cfdi_values['cadena'])
            decoded_cfdi_values['cfdi_node'].attrib['Sello'] = cfdi_values['certificate'].sudo()._sign(decoded_cfdi_values['cadena'], formatting='base64')

            cfdi_str = etree.tostring(decoded_cfdi_values['cfdi_node'], pretty_print=True, xml_declaration=True, encoding='UTF-8')
            #_logger.info('cfdi_str %s', cfdi_str)
            # == Check credentials ==
            root_company = invoice.company_id
            pac_name = root_company.l10n_mx_edi_pac
            if pac_name == 'sw':
                credentials = invoice._get_sw_credentials(root_company)
            elif pac_name == 'finkok':
                credentials = invoice._get_finkok_credentials(root_company)
            else:
                raise UserError(_("No está configurado el PAC Solucion Factible"))

            if credentials.get('errors'):
                raise UserError(_("Error: %s") % (credentials['errors']))

            # == Check PAC ==
            if pac_name == 'sw':
                sign_results = invoice._sw_sign(credentials, cfdi_str)
            elif pac_name == 'finkok':
                sign_results = invoice._finkok_sign(credentials, cfdi_str)

            if sign_results.get('errors'):
                raise UserError(_("Error 2: %s") % (sign_results['errors']))

            # == Success ==
            #_logger.info('sign_results %s', sign_results)
            #on_success(cfdi_values, cfdi_filename, sign_results['cfdi_str'], populate_return=populate_return)

            # Receive and store XML invoice
            if sign_results['cfdi_str']:
                invoice._set_data_from_xml(sign_results['cfdi_str'])
#                self._set_data_from_xml(base64.b64decode(sign_results['cfdi_str']))
                file_name = invoice.number.replace('/', '_') + '.xml'
                self.env['ir.attachment'].sudo().create(
                    {
                        'name': file_name,
                        'datas': base64.b64encode(sign_results['cfdi_str']),
                        # 'datas_fname': file_name,
                        'res_model': invoice._name,
                        'res_id': invoice.id,
                        'type': 'binary'
                    })

            invoice.write({'estado_factura': 'factura_correcta',
                           'factura_cfdi': True,
                           })
            invoice.message_post(body="CFDI emitido")
        return True

    def action_cfdi_cancel(self):
        for invoice in self:
            if invoice.factura_cfdi:
                if invoice.estado_factura == 'factura_cancelada':
                    pass
                    # raise UserError(_('La factura ya fue cancelada, no puede volver a cancelarse.'))
                root_company = self.company_id
                pac_name = root_company.l10n_mx_edi_pac
                if pac_name == 'sw':
                    credentials = self._get_sw_credentials(root_company)
                elif pac_name == 'finkok':
                    credentials = self._get_finkok_credentials(root_company)
                else:
                    raise UserError(_("No está configurado el PAC Solucion Factible"))
                if credentials.get('errors'):
                    raise UserError(_("Error: %s") % (credentials['errors']))
                cfdi_values = self.env['l10n_mx_edi.document']._get_company_cfdi_values(root_company)
                self.env['l10n_mx_edi.document']._add_certificate_cfdi_values(cfdi_values)
                if pac_name == 'sw':
                    json_response = self._sw_cancel(cfdi_values, credentials, invoice.folio_fiscal, self.env.context.get('motivo_cancelacion','02'), cancel_uuid=self.env.context.get('foliosustitucion',''))
                elif pac_name == 'finkok':
                    json_response = self._finkok_cancel(root_company, credentials, invoice.folio_fiscal, self.env.context.get('motivo_cancelacion','02'), cancel_uuid=self.env.context.get('foliosustitucion',''))

                #_logger.info('json response %s', json_response)
                log_msg = ''
                if pac_name == 'sw':
                    if json_response['status'] != 'success':
                        raise UserError(_("Error en la cancelación"))
                elif pac_name == 'finkok':
                    #_logger.info('json_response %s', json_response)
                    if 'errors' in json_response:
                        raise UserError(_("Error en la cancelación %s") % (json_response.get('errors', {})))
                if pac_name == 'sw':
                    file_name = 'CANCEL_' + invoice.number.replace('/', '_') + '.xml'
                    self.env['ir.attachment'].sudo().create(
                        {
                            'name': file_name,
                            'datas': base64.b64encode(json_response.get('data', {}).get('acuse', {}).encode("utf-8")),
                            # 'datas_fname': file_name,
                            'res_model': self._name,
                            'res_id': invoice.id,
                            'type': 'binary'
                        })
                self.message_post(body="CFDI Cancelado")
                invoice.write({'estado_factura': 'factura_cancelada'})
   
    def send_factura_mail(self):
        self.ensure_one()
        template = self.env.ref('l10n_mx_traslado.email_template_factura_traslado', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)

        ctx = dict()
        ctx.update({
            'default_model': 'cfdi.traslado',
            'default_res_ids': self.ids,
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def unlink(self):
        raise UserError("Los registros no se pueden borrar, solo cancelar.")

    def llenar_id_ubicacion(self):
        for traslado in self:
            orig = 1
            dest = 1
            for line in traslado.ubicaciones_line_ids:
                if line.tipoubicacion == 'Origen':
                    line.idubicacion = 'OR' + str(orig).rjust(6, '0')
                    orig += 1
                else:
                    line.idubicacion = 'DE' + str(dest).rjust(6, '0')
                    dest += 1

    @api.onchange('ubicaciones_line_ids')
    def _compute_distancia(self):
        for traslado in self:
            distancia = 0
            contacto_previo = None
            for line in traslado.ubicaciones_line_ids:
                if line.tipoubicacion == 'Origen':
                    contacto_previo =  line.contacto
                if line.tipoubicacion == 'Destino':
                    if contacto_previo and line.contacto:
                        if contacto_previo.cce_latitud and contacto_previo.cce_longitud and line.contacto.cce_latitud and line.contacto.cce_longitud:
                            line.distanciarecorrida = self.haversine_distance(contacto_previo.cce_latitud, 
                                                                              contacto_previo.cce_longitud, 
                                                                              line.contacto.cce_latitud, 
                                                                              line.contacto.cce_longitud)

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great-circle distance between two points 
        on the earth (specified in decimal degrees).
        """
        # Radius of the Earth in kilometers
        R = 6371.0 

        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Differences in coordinates
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad

        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    # -------------------------------------------------------------------------
    # CFDI: PACs
    # -------------------------------------------------------------------------

    @api.model
    def _get_finkok_credentials(self, company):
        ''' Return the company credentials for PAC: finkok. Does not depend on a recordset
        '''
        if company.l10n_mx_edi_pac_test_env:
            return {
                'username': 'cfdi@vauxoo.com',
                'password': 'vAux00__',
                'sign_url': 'http://demo-facturacion.finkok.com/servicios/soap/stamp.wsdl',
                'cancel_url': 'http://demo-facturacion.finkok.com/servicios/soap/cancel.wsdl',
            }
        else:
            if not company.sudo().l10n_mx_edi_pac_username or not company.sudo().l10n_mx_edi_pac_password:
                return {
                    'errors': [_("The username and/or password are missing.")]
                }

            return {
                'username': company.sudo().l10n_mx_edi_pac_username,
                'password': company.sudo().l10n_mx_edi_pac_password,
                'sign_url': 'http://facturacion.finkok.com/servicios/soap/stamp.wsdl',
                'cancel_url': 'http://facturacion.finkok.com/servicios/soap/cancel.wsdl',
            }

    @api.model
    def _finkok_sign(self, credentials, cfdi):
        ''' Send the CFDI XML document to Finkok for signature. Does not depend on a recordset
        '''
        def get_in_error(error, key):
            if key in error:
                return error[key]

        try:
            client = Client(credentials['sign_url'], timeout=20)
            response = client.service.stamp(cfdi, credentials['username'], credentials['password'])
            # pylint: disable=broad-except
        except Exception as e:
            return {
                'errors': [_("The Finkok service failed to sign with the following error: %s", str(e))],
            }

        if response.Incidencias and not response.xml:
            error = response.Incidencias.Incidencia[0]

            code = get_in_error(error, 'CodigoError')
            msg = get_in_error(error, 'MensajeIncidencia')
            extra = get_in_error(error, 'ExtraInfo')

            errors = []
            if code:
                errors.append(_("Code : %s", code))
            if msg:
                errors.append(_("Message : %s", msg))
            if extra:
                errors.append(_("Extra Info : %s", extra))
            return {'errors': errors}

        cfdi_signed = response.xml if 'xml' in response else None
        if cfdi_signed:
            cfdi_signed = cfdi_signed.encode('utf-8')

        return {
            'cfdi_str': cfdi_signed,
        }

    @api.model
    def _finkok_cancel(self, cfdi_values, credentials, uuid, cancel_reason, cancel_uuid=None):
        company = cfdi_values['root_company']
        certificate_sudo = cfdi_values['certificate'].sudo()
        cer_pem = base64.b64decode(certificate_sudo.pem_certificate)
        key_pem = self._get_unencrypted_private_key_pem(certificate_sudo.private_key_id)

        try:
            client = Client(credentials['cancel_url'], timeout=20)
            factory = client.type_factory('apps.services.soap.core.views')
            uuid_type = factory.UUID()
            uuid_type.UUID = uuid
            uuid_type.Motivo = cancel_reason
            if cancel_uuid:
                uuid_type.FolioSustitucion = cancel_uuid
            docs_list = factory.UUIDArray(uuid_type)
            response = client.service.cancel(
                docs_list,
                credentials['username'],
                credentials['password'],
                company.vat,
                cer_pem,
                key_pem,
            )
            # pylint: disable=broad-except
        except Exception as e:
            return {
                'errors': [_("The Finkok service failed to cancel with the following error: %s", str(e))],
            }

        code = None
        msg = None
        if 'Folios' in response and response.Folios:
            if 'EstatusUUID' in response.Folios.Folio[0]:
                response_code = response.Folios.Folio[0].EstatusUUID
                if response_code not in ('201', '202'):
                    code = response_code
                    msg = _("Cancelling got an error")
        elif 'CodEstatus' in response:
            code = response.CodEstatus
            msg = _("Cancelling got an error")
        else:
            msg = _('A delay of 2 hours has to be respected before to cancel')

        errors = []
        if code:
            errors.append(_("Code : %s", code))
        if msg:
            errors.append(_("Message : %s", msg))
        if errors:
            return {'errors': errors}

        return {}

    @api.model
    def _get_solfact_credentials(self, company):
        ''' Return the company credentials for PAC: solucion factible. Does not depend on a recordset
        '''
        if company.l10n_mx_edi_pac_test_env:
            return {
                'username': 'testing@solucionfactible.com',
                'password': 'timbrado.SF.16672',
                'url': 'https://testing.solucionfactible.com/ws/services/Timbrado?wsdl',
            }
        else:
            if not company.sudo().l10n_mx_edi_pac_username or not company.sudo().l10n_mx_edi_pac_password:
                return {
                    'errors': [_("The username and/or password are missing.")]
                }

            return {
                'username': company.sudo().l10n_mx_edi_pac_username,
                'password': company.sudo().l10n_mx_edi_pac_password,
                'url': 'https://solucionfactible.com/ws/services/Timbrado?wsdl',
            }

    @api.model
    def _solfact_sign(self, credentials, cfdi):
        ''' Send the CFDI XML document to Solucion Factible for signature. Does not depend on a recordset
        '''
        try:
            client = Client(credentials['url'], timeout=20)
            response = client.service.timbrar(credentials['username'], credentials['password'], cfdi, False)
            # pylint: disable=broad-except
        except Exception as e:
            return {
                'errors': [_("The Solucion Factible service failed to sign with the following error: %s", str(e))],
            }

        if response.status != 200:
            # ws-timbrado-timbrar - status 200 : CFDI correctamente validado y timbrado.
            return {
                'errors': [_("The Solucion Factible service failed to sign with the following error: %s", response.mensaje)],
            }

        if response.resultados:
            result = response.resultados[0]
        else:
            result = response

        cfdi_signed = result.cfdiTimbrado if 'cfdiTimbrado' in result else None
        if cfdi_signed:
            return {
                'cfdi_str': cfdi_signed,
            }

        msg = result.mensaje if 'mensaje' in result else None
        code = result.status if 'status' in result else None
        errors = []
        if code:
            errors.append(_("Code : %s", code))
        if msg:
            errors.append(_("Message : %s", msg))
        return {'errors': errors}

    @api.model
    def _solfact_cancel(self, cfdi_values, credentials, uuid, cancel_reason, cancel_uuid=None):
        certificate = cfdi_values['certificate']
        uuid_param = f"{uuid}|{cancel_reason}|"
        if cancel_uuid:
            uuid_param += cancel_uuid
        cer_pem = base64.b64decode(certificate.pem_certificate)
        key_pem = self._get_unencrypted_private_key_pem(certificate.private_key_id)
        key_password = certificate.private_key_id.password

        try:
            client = Client(credentials['url'], timeout=20)
            response = client.service.cancelar(
                credentials['username'], credentials['password'],
                uuid_param, cer_pem, key_pem, key_password
            )
            # pylint: disable=broad-except
        except Exception as e:
            return {
                'errors': [_("The Solucion Factible service failed to cancel with the following error: %s", str(e))],
            }

        if response.status not in (200, 201):
            # ws-timbrado-cancelar - status 200 : El proceso de cancelación se ha completado correctamente.
            # ws-timbrado-cancelar - status 201 : El folio se ha cancelado con éxito.
            return {
                'errors': [_("The Solucion Factible service failed to cancel with the following error: %s", response.mensaje)],
            }

        if response.resultados:
            response_code = response.resultados[0].statusUUID if 'statusUUID' in response.resultados[0] else None
        else:
            response_code = response.status if 'status' in response else None

        # no show code and response message if cancel was success
        msg = None
        code = None
        if response_code not in ('201', '202'):
            code = response_code
            if response.resultados:
                result = response.resultados[0]
            else:
                result = response
            if 'mensaje' in result:
                msg = result.mensaje

        errors = []
        if code:
            errors.append(_("Code : %s", code))
        if msg:
            errors.append(_("Message : %s", msg))
        if errors:
            return {'errors': errors}

        return {}

    @api.model
    def _document_get_sw_token(self, credentials):
        if credentials['password'] and not credentials['username']:
            # token is configured directly instead of user/password
            return {
                'token': credentials['password'].strip(),
            }

        try:
            headers = {
                'user': credentials['username'],
                'password': credentials['password'],
                'Cache-Control': "no-cache"
            }
            response = requests.post(credentials['login_url'], headers=headers, timeout=20)
            response.raise_for_status()
            response_json = response.json()
            return {
                'token': response_json['data']['token'],
            }
        except (requests.exceptions.RequestException, KeyError, TypeError) as req_e:
            return {
                'errors': [str(req_e)],
            }

    @api.model
    def _get_sw_credentials(self, company):
        '''Get the company credentials for PAC: SW. Does not depend on a recordset
        '''
        if not company.sudo().l10n_mx_edi_pac_username or not company.sudo().l10n_mx_edi_pac_password:
            return {
                'errors': [_("The username and/or password are missing.")]
            }

        credentials = {
            'username': company.sudo().l10n_mx_edi_pac_username,
            'password': company.sudo().l10n_mx_edi_pac_password,
        }

        if company.l10n_mx_edi_pac_test_env:
            credentials.update({
                'login_url': 'https://services.test.sw.com.mx/security/authenticate',
                'sign_url': 'https://services.test.sw.com.mx/cfdi33/stamp/v3/b64',
                'cancel_url': 'https://services.test.sw.com.mx/cfdi33/cancel/csd',
            })
        else:
            credentials.update({
                'login_url': 'https://services.sw.com.mx/security/authenticate',
                'sign_url': 'https://services.sw.com.mx/cfdi33/stamp/v3/b64',
                'cancel_url': 'https://services.sw.com.mx/cfdi33/cancel/csd',
            })

        # Retrieve a valid token.
        credentials.update(self._document_get_sw_token(credentials))

        return credentials

    @api.model
    def _document_sw_call(self, url, headers, payload=None):
        try:
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                verify=True,
                timeout=20,
            )
        except requests.exceptions.RequestException as req_e:
            return {'status': 'error', 'message': str(req_e)}
        msg = ""
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as res_e:
            msg = str(res_e)
        try:
            response_json = response.json()
        except JSONDecodeError:
            # If it is not possible get json then
            # use response exception message
            return {'status': 'error', 'message': msg}
        if (response_json['status'] == 'error' and
                response_json['message'].startswith('307')):
            # XML signed previously
            cfdi = base64.encodebytes(
                response_json['messageDetail'].encode('UTF-8'))
            cfdi = cfdi.decode('UTF-8')
            response_json['data'] = {'cfdi': cfdi}
            # We do not need an error message if XML signed was
            # retrieved then cleaning them
            response_json.update({
                'message': None,
                'messageDetail': None,
                'status': 'success',
            })
        return response_json

    @api.model
    def _sw_sign(self, credentials, cfdi):
        ''' calls the SW web service to send and sign the CFDI XML.
        Method does not depend on a recordset
        '''
        cfdi_b64 = base64.encodebytes(cfdi).decode('UTF-8')
        random_values = [random.choice(string.ascii_letters + string.digits) for n in range(30)]
        boundary = ''.join(random_values)
        payload = """--%(boundary)s
Content-Type: text/xml
Content-Transfer-Encoding: binary
Content-Disposition: form-data; name="xml"; filename="xml"

%(cfdi_b64)s
--%(boundary)s--
""" % {'boundary': boundary, 'cfdi_b64': cfdi_b64}
        payload = payload.replace('\n', '\r\n').encode('UTF-8')

        headers = {
            'Authorization': "bearer " + credentials['token'],
            'Content-Type': ('multipart/form-data; '
                             'boundary="%s"') % boundary,
        }

        response_json = self._document_sw_call(credentials['sign_url'], headers, payload=payload)
        #_logger.info('response_json %s', response_json)
        try:
            cfdi_signed = response_json['data']['cfdi']
        except (KeyError, TypeError):
            cfdi_signed = None

        if cfdi_signed:
            return {
                'cfdi_str': base64.decodebytes(cfdi_signed.encode('UTF-8')),
            }
        else:
            code = response_json.get('message')
            msg = response_json.get('messageDetail')
            errors = []
            if code:
                errors.append(_("Code : %s", code))
            if msg:
                errors.append(_("Message : %s", msg))
            return {'errors': errors}

    @api.model
    def _sw_cancel(self, cfdi_values, credentials, uuid, cancel_reason, cancel_uuid=None):
        company = cfdi_values['root_company']
        certificate_sudo = cfdi_values['certificate'].sudo()
        headers = {
            'Authorization': "bearer " + credentials['token'],
            'Content-Type': "application/json"
        }
        payload_dict = {
            'rfc': company.vat,
            'b64Cer': certificate_sudo.pem_certificate.decode('UTF-8'),
            'b64Key': certificate_sudo.private_key_id.pem_key.decode('UTF-8'),
            'password': certificate_sudo.private_key_id.password,
            'uuid': uuid,
            'motivo': cancel_reason,
        }
        if cancel_uuid:
            payload_dict['folioSustitucion'] = cancel_uuid
        payload = json.dumps(payload_dict)

        response_json = self._document_sw_call(credentials['cancel_url'], headers, payload=payload.encode('UTF-8'))

        cancelled = response_json['status'] == 'success'
        if cancelled:
            data_codes = response_json.get('data', {}).get('uuid', {}).values()
            data_code = next(iter(data_codes)) if data_codes else ''
            code = '' if data_code in ('201', '202') else data_code
            msg = '' if data_code in ('201', '202') else _("Cancelling got an error")
        else:
            code = response_json.get('message')
            msg = response_json.get('messageDetail')
        errors = []
        if code:
            errors.append(_("Code : %s", code))
        if msg:
            errors.append(_("Message : %s", msg))
        if errors:
            return {'errors': errors}

        return response_json

    @api.model
    def _get_unencrypted_private_key_pem(self, key):
        return serialization.load_pem_private_key(
            base64.b64decode(key.pem_key),
            key.password.encode() if key.password else None,
        ).private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )


class CfdiTrasladoMail(models.Model):
    _name = "cfdi.traslado.mail"
    _inherit = ['mail.thread']
    _description = "CFDI Traslado Mail"

    factura_id = fields.Many2one('cfdi.traslado', string='CFDI Traslado')
    name = fields.Char(related='factura_id.number')
    partner_id = fields.Many2one(related='factura_id.partner_id')
    company_id = fields.Many2one(related='factura_id.company_id')


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _compute_attachment_ids(self):
        res = super(MailComposeMessage, self)._compute_attachment_ids()
        for rec in self:
            if self.model == 'cfdi.traslado':
                attachment_ids=[]
                template_id = self.env.ref('l10n_mx_traslado.email_template_factura_traslado')
                if self.template_id.id == template_id.id:
                    res_ids = ast.literal_eval(self.res_ids)
                    for res_id in res_ids:
                        invoice = self.env[self.model].browse(res_id)
                        domain = [
                            ('res_id', '=', invoice.id),
                            ('res_model', '=', invoice._name),
                            ('name', '=', invoice.number.replace('/', '_') + '.xml')]
                        xml_file = self.env['ir.attachment'].search(domain, limit=1)
                        if xml_file:
                            attachment_ids.extend(rec.attachment_ids.ids)
                            attachment_ids.append(xml_file.id)
                    if attachment_ids:
                        rec.attachment_ids = [(6, 0, attachment_ids)]
        return res

