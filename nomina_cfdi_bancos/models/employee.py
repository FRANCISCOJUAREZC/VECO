# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Employee(models.Model):
    _inherit = "hr.employee"

    dispersion_nombre = fields.Char("Nombre")
    dispersion_paterno = fields.Char("Apellido Paterno")
    dispersion_materno = fields.Char("Apellido Materno")

    clave_santander_banco = fields.Char("Clave del banco de la cuenta de abono (Santander)")
    plaza_santander_banco = fields.Char("Número de la plaza Banxico de la cuenta (Santander)")