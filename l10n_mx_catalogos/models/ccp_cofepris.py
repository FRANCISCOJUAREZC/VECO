# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CcpRegistroIstmo(models.Model):
    _name = 'ccp.sector.cofepris'
    _rec_name = "descripcion"
    _description = 'ccp sector cofepris'

    clave = fields.Char(string='Clave')
    descripcion = fields.Char(string='Descripción')
