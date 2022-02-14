# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
import datetime

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    dias_pagar = fields.Float(string='Dias a pagar', store=True,digits=(0,4))
    imss_dias = fields.Float(string='Dias a cotizar en la nómina', store=True,digits=(0,4))
    imss_mes = fields.Float(string='Dias en el mes', store=True,digits=(0,4))

    @api.onchange('periodicidad_pago', 'tipo_configuracion')
    def _dias_pagar(self):
        if self.periodicidad_pago:
            if self.periodicidad_pago == '01':
                self.dias_pagar = 1
            elif self.periodicidad_pago == '02':
                self.dias_pagar = 7.0192
            elif self.periodicidad_pago == '03':
                self.dias_pagar = 14
            elif self.periodicidad_pago == '04':
                if self.tipo_configuracion.tipo_pago == '01':
                    self.dias_pagar = 15
                    self.imss_dias = self.imss_mes / 2
                elif self.tipo_configuracion.tipo_pago == '02':
                    delta = self.date_end - self.date_start
                    self.dias_pagar = delta.days + 1
                    self.imss_dias = delta.days + 1
                else:
                    self.dias_pagar = 15.2083
                    self.imss_dias = 15.2083
            elif self.periodicidad_pago == '05':
                if self.tipo_configuracion.tipo_pago == '01':
                    self.dias_pagar = 30
                elif self.tipo_configuracion.tipo_pago == '02':
                    delta = self.date_end - self.date_start
                    self.dias_pagar = delta.days + 1
                else:
                    self.dias_pagar = 30.4166
            else:
                delta = self.date_end - self.date_start
                self.dias_pagar = delta.days + 1
    
class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'
    
    number_of_days = fields.Float(string='Number of Days',digits=(0,4))
	
class ConfiguracionNomina(models.Model):
    _inherit = 'configuracion.nomina'

    imss_dias = fields.Float(string='Dias a cotizar en la nómina', store=True, digits=(0,4))
    imss_mes = fields.Float(string='Dias en el mes', store=True, digits=(0,4))

