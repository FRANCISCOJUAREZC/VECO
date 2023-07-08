# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CveFiguraTransporte(models.Model):
    _name = 'cve.figura.transporte'
    _rec_name = "descripcion"
    _description = 'cvefiguratransporte'

    clave = fields.Char(string='Clave')
    descripcion = fields.Char(string='Descripción')
