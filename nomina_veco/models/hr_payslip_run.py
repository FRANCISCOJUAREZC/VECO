# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
import datetime

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    dias_pagar = fields.Float(string='Dias a pagar', store=True,digits=(0,4))
    imss_dias = fields.Float(string='Dias a cotizar en la nómina', store=True,digits=(0,4))
    imss_mes = fields.Float(string='Dias en el mes', store=True,digits=(0,4))

class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'
    
    number_of_days = fields.Float(string='Number of Days',digits=(0,4))

class ConfiguracionNomina(models.Model):
    _inherit = 'configuracion.nomina'

    imss_dias = fields.Float(string='Dias a cotizar en la nómina', store=True, digits=(0,4))
    imss_mes = fields.Float(string='Dias en el mes', store=True, digits=(0,4))

