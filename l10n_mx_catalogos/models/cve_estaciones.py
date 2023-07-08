# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CveEstaciones(models.Model):
    _name = 'cve.estaciones'
    _rec_name = "descripcion"
    _description = 'cvecestaciones'

    clave_identificacion = fields.Char(string='Clave estaciones')
    descripcion = fields.Char(string='Descripción')
    clave_transporte = fields.Char(string='Clave transporte')
