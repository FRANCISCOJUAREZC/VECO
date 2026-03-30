# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CcpFormaFarma(models.Model):
    _name = 'ccp.forma.farma'
    _rec_name = "descripcion"
    _description = 'ccp farma'

    clave = fields.Char(string='Clave')
    descripcion = fields.Char(string='Descripción')
