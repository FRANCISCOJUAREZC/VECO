# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import format_date

import logging
_logger = logging.getLogger(__name__)

class HrPayslipEmployeesExt(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    
    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': from_date.strftime('%B %Y'),
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        contracts = employees._get_contracts(
            payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
        ).filtered(lambda c: c.active)
        contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end),
            ('date_stop', '>=', payslip_run.date_start),
            ('employee_id', 'in', employees.ids),
        ])
        self._check_undefined_slots(work_entries, payslip_run)

        if(self.structure_id.type_id.default_struct_id == self.structure_id):
            work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
            if work_entries._check_if_error():
                work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])

                for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
                    work_entries_by_contract[work_entry.contract_id] |= work_entry

                for contract, work_entries in work_entries_by_contract.items():
                    conflicts = work_entries._to_intervals()
                    time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in conflicts._items]])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Some work entries could not be validated.'),
                        'message': _('Time intervals to look for:%s', time_intervals_str),
                        'sticky': False,
                    }
                }


        default_values = Payslip.default_get(Payslip.fields_get())
        payslip_values = [dict(default_values, **{
            'name': 'Payslip - %s' % (contract.employee_id.name),
            'employee_id': contract.employee_id.id,
            'credit_note': payslip_run.credit_note,
            'payslip_run_id': payslip_run.id,
            'date_from': payslip_run.date_start,
            'date_to': payslip_run.date_end,
            'contract_id': contract.id,
            'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            'dias_pagar': payslip_run.dias_pagar,
            'imss_mes': payslip_run.imss_mes,
            'imss_dias': payslip_run.imss_dias,
            'ultima_nomina': payslip_run.ultima_nomina,
            'mes': payslip_run.mes,
            #'isr_devolver': payslip_run.isr_devolver,
            'isr_ajustar': payslip_run.isr_ajustar,
            'isr_anual': payslip_run.isr_anual,
            'periodicidad_pago': payslip_run.periodicidad_pago,
            #'no_periodo': payslip_run.no_periodo,
            'concepto_periodico': payslip_run.concepto_periodico,
            'tipo_nomina' : payslip_run.tipo_nomina,
            'fecha_pago' : payslip_run.fecha_pago,
        }) for contract in contracts]

        payslips = Payslip.with_context(tracking_disable=True).create(payslip_values)
        for payslip in payslips:
          #  payslip._onchange_employee()
            
            ######################## agregar prima vacacional
            # compute Prima vacacional en fecha correcta
            if payslip.contract_id.tipo_prima_vacacional == '01':
                date_start = payslip.contract_id.date_start
                if date_start:
                    d_from = fields.Date.from_string(payslip_run.date_start)
                    d_to = fields.Date.from_string(payslip_run.date_end)

                    date_start = fields.Date.from_string(date_start)
                    if datetime.datetime.today().year > date_start.year:
                        if str(date_start.day) == '29' and str(date_start.month) == '2':
                            date_start -=  datetime.timedelta(days=1)
                        date_start = date_start.replace(d_to.year)
                        
                        if d_from <= date_start <= d_to:
                            diff_date = payslip_run.date_end - payslip.contract_id.date_start #datetime.datetime.combine(, datetime.time.max)
                            years = diff_date.days /365.0
                            antiguedad_anos = int(years)
                            tabla_antiguedades =  payslip.contract_id.tablas_cfdi_id.tabla_antiguedades.filtered(lambda x: x.antiguedad <= antiguedad_anos)
                            tabla_antiguedades = tabla_antiguedades.sorted(lambda x:x.antiguedad, reverse=True)
                            vacaciones = tabla_antiguedades and tabla_antiguedades[0].vacaciones or 0
                            prima_vac = tabla_antiguedades and tabla_antiguedades[0].prima_vac or 0

                            work_entry_type = self.env['hr.work.entry.type'].sudo().search([('code','=','PVC')])
                            attendances = {
                                 'payslip_id': payslip.id,
                                 'sequence': 2,
                                 'work_entry_type_id': work_entry_type.id,
                                 'number_of_days': vacaciones * prima_vac / 100.0, #work_data['days'],
                                #'number_of_hours': 1['hours'],
                                # 'contract_id': contract.id,
                            }
                            new_worked_days = self.env['hr.payslip.worked_days'].create(attendances)

            ######################## Revisar dias nomina
            for worklines in payslip.worked_days_line_ids:
                if worklines.work_entry_type_id.code == 'WORK100':
                    if payslip_run.tipo_nomina == 'O':
                       if worklines.number_of_days != 15:
                             worklines.number_of_days = 15
                    else:
                       if self.structure_id.name != 'Aguinaldo':
                          days = 0
                          if payslip.contract_id.date_start > payslip_run.date_start:
                              days = payslip_run.date_end - payslip.contract_id.date_start
                          else:
                              days = payslip_run.date_end - payslip_run.date_start
                          worklines.number_of_days = days.days + 1
                       else:
                          days = 0
                          if payslip.contract_id.date_start > payslip_run.date_start:
                              days_compute = payslip_run.date_end - payslip.contract_id.date_start
                              days = days_compute.days + 1
                          else:
                              days = 365
                          worklines.number_of_days = days

        payslips.compute_sheet()
        payslip_run.state = 'draft'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }

