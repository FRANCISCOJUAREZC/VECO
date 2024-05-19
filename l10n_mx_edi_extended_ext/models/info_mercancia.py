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

#                                        <t t-if="good_details['desc_especifica']">
#                                            <t t-foreach="good_details['desc_especifica']" t-as="info_merc">
#                                                <cce20:DescripcionesEspecificas
#                                                    t-att-Marca="info_merc['Marca']"
#                                                    t-att-Modelo="info_merc['Modelo']"
#                                                    t-att-SubModelo="info_merc['SubModelo']"
#                                                    t-att-NumeroSerie="info_merc['NumeroSerie']"/>
#                                            </t>
#                                        </t>