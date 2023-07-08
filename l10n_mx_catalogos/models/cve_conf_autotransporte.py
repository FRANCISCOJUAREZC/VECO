# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CveConfAutotransporte(models.Model):
    _name = 'cve.conf.autotransporte'
    _rec_name = "descripcion"
    _description = 'cvecconfauto'

    clave = fields.Char(string='Clave')
    descripcion = fields.Char(string='Descripción')
