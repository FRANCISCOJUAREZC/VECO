# -*- coding: utf-8 -*-
from odoo import models, fields, _


class FaltasNomina(models.Model):
    _name = 'faltas.nomina'
    _description = 'Faltas Nomina'

    name = fields.Char('Folio', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')
    dias = fields.Integer('Días')
    tipo_de_falta = fields.Selection(
        [('Justificada con goce de sueldo', 'Justificada con goce de sueldo'),
         ('Justificada sin goce de sueldo', 'Justificada sin goce de sueldo'),
         ('Injustificada', 'Injustificada')],
        string='Tipo de falta')
    state = fields.Selection(
        [('draft', 'Borrador'), ('done', 'Hecho'), ('cancel', 'Cancelado')],
        string='Estado', default='draft')
