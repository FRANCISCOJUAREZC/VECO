# -*- coding: utf-8 -*-
from odoo import fields, models, api

class InfoSerieMercancias(models.Model):
    _name = 'account.move.mercancias.series'
    _rec_name = "cce_numeroserie"

    cce_numeroserie = fields.Char(string='Número de serie')	
    order_id = fields.Many2one('account.move.mercancias.info', string='Serie', ondelete='cascade', index=True, copy=False)

class InfoMercancias(models.Model):
    _name = 'account.move.mercancias.info'
    _rec_name = "nombre"

    nombre = fields.Char(string='Nombre')
    cce_marca = fields.Char(string='Marca')
    cce_modelo = fields.Char(string='Modelo')
    cce_submodelo = fields.Char(string='SubModelo')
    cce_series = fields.One2many('account.move.mercancias.series', 'order_id', 'Series Mercancias', copy=True, readonly=False)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    info_mercancias = fields.Many2one('account.move.mercancias.info', string='Información mercancia')

# cfdiv40_extended
#                            <cce20:Mercancias>
#                                <t t-foreach="ext_trade_goods_details" t-as="good_details">
#                                    <t t-set="product" t-value="good_details['product']"/>
#                                    <cce20:Mercancia t-att-NoIdentificacion="format_string(product.default_code, 100)" t-att-FraccionArancelaria="product.l10n_mx_edi_tariff_fraction_id.code" t-att-CantidadAduana="format_float(good_details['quantity_aduana'], 3)" t-att-UnidadAduana="product.l10n_mx_edi_umt_aduana_id.l10n_mx_edi_code_aduana" t-att-ValorUnitarioAduana="format_float(good_details['price_unit_usd'], 6)" t-att-ValorDolares="format_float(good_details['line_total_usd'], 4)">
#                                        <t t-if="good_details['desc_especifica']">
#                                            <t t-foreach="good_details['desc_especifica']" t-as="info_merc">
#                                                <cce20:DescripcionesEspecificas
#                                                    t-att-Marca="info_merc['Marca']"
#                                                    t-att-Modelo="info_merc['Modelo']"
#                                                    t-att-SubModelo="info_merc['SubModelo']"
#                                                    t-att-NumeroSerie="info_merc['NumeroSerie']"/>
#                                            </t>
#                                        </t>
#                                    </cce20:Mercancia>
#                                </t>
#                            </cce20:Mercancias>