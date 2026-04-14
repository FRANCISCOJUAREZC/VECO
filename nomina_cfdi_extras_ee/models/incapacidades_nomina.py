# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class IncapacidadesNomina(models.Model):
    _name = 'incapacidades.nomina'
    _description = 'Incapacidades Nomina'

    name = fields.Char('Folio', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    fecha = fields.Date('Fecha')
    ramo_de_seguro = fields.Selection(
        [('Riesgo de trabajo', 'Riesgo de trabajo'),
         ('Enfermedad general', 'Enfermedad general'),
         ('Maternidad', 'Maternidad')],
        string='Ramo de seguro')
    tipo_de_riesgo = fields.Selection(
        [('Accidente de trabajo', 'Accidente de trabajo'),
         ('Accidente de trayecto', 'Accidente de trayecto'),
         ('Enfermedad de trabajo', 'Enfermedad de trabajo')],
        string='Tipo de riesgo')
    secuela = fields.Selection(
        [('Ninguna', 'Ninguna'),
         ('Incapacidad temporal', 'Incapacidad temporal'),
         ('Valuación inicial provisional', 'Valuación inicial provisional'),
         ('Valuación inicial definitiva', 'Valuación inicial definitiva')],
        string='Secuela')
    control = fields.Selection(
        [('Unica', 'Unica'),
         ('Inicial', 'Inicial'),
         ('Subsecuente', 'Subsecuente'),
         ('Alta médica o ST-2', 'Alta médica o ST-2')],
        string='Control incapacidad')
    control2 = fields.Selection(
        [('01', 'Prenatal o ST-3'),
         ('02', 'Enalce'),
         ('03', 'Postnatal')],
        string='Control maternidad')
    porcentaje = fields.Char('Porcentaje')
    dias = fields.Integer('Días')
    descripcion = fields.Text('Descripción')
    folio_incapacidad = fields.Char('Folio de incapacidad')
    state = fields.Selection(
        [('draft', 'Borrador'), ('done', 'Hecho'), ('cancel', 'Cancelado')],
        string='Estado', default='draft')
