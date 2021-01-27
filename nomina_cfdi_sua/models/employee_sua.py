# -*- coding: utf-8 -*-
# Copyright 2012 - 2013 Daniel Reis
# Copyright 2015 - Antiun Ingeniería S.L. - Sergio Teruel
# Copyright 2016 - Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

class Employee(models.Model):
    _inherit = "hr.employee"

    nombreEmpleado = fields.Char(_('Nombre'))
    apellido_Paterno = fields.Char(_('Apellido Paterno'))
    apellido_Materno = fields.Char(_('Apellido Materno'))
    unidadMedicina = fields.Char(_('Unidad de medicina familiar'))
    no_guia = fields.Char(_('Guia'))


    tipoDeTrabajador = fields.Selection(
        selection=[('1', '1 - Trabajador permanente'),
                   ('2', '2 - Trabajador en ciudad'),
                   ('3', '3 - Trabajador en construccion'),
                   ('4', '4 - Eventual de campo'),],
        string=_('Tipo de trabajador'),
    )
    tipoDeSalario = fields.Selection(
        selection=[('0', '0 - Salario fijo'),
                   ('1', '1 - Salario variable'),
                   ('2', '2 - Salario mixto'),],
        string=_('Tipo de salario'),
    )
    tipoDeJornada = fields.Selection(
        selection=[('1', '1 - Un dia'),
                   ('2', '2 - Dos dias'),
                   ('3', '3 - Tres dias'),
                   ('4', '4 - Cuatro dias'),
                   ('5', '5 - Cinco dias'),
                   ('6', '6 - Jornada reducida'),
                   ('7', '7 - Jornada normal'),],
        string=_('Tipo de jornada'),
    )

