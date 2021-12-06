# -*- coding: utf-8 -*-


from odoo import fields, models, api,_


class ResPartner(models.Model):
    _inherit = 'res.partner'

    codigotransportista = fields.Many2one('cve.codigo.transporte.aereo',string='Código transportista')
    cce_licencia = fields.Char(string=_('No. licencia'))
