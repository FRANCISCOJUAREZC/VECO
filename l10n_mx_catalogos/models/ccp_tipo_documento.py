# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CcpTipoDocumento(models.Model):
    _name = 'ccp.tipo.documento'
    _rec_name = "descripcion"
    _description = 'ccp tipo documento'

    clave = fields.Char(string='Clave')
    descripcion = fields.Char(string='Descripción')
