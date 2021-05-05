# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import datetime
from datetime import timedelta, date
from datetime import time as datetime_time
import logging
_logger = logging.getLogger(__name__)
from collections import defaultdict
from pytz import timezone
import pytz

class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    dias_pagar = fields.Float('Pagar en la nomina', digits=(0,4))
    imss_dias = fields.Float('Cotizar en el IMSS',default='15', digits=(0,4))

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        horas_obj = self.env['horas.nomina']
        tipo_de_hora_mapping = {'1':'HEX1', '2':'HEX2', '3':'HEX3'}
        
        def is_number(s):
            try:
                return float(s)
            except ValueError:
                return 0

        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.datetime.combine(fields.Date.from_string(date_from), datetime.time.min)
            day_to = datetime.datetime.combine(fields.Date.from_string(date_to), datetime.time.max)
            nb_of_days = (day_to - day_from).days + 1

            # compute Prima vacacional en fecha correcta
            if contract.tipo_prima_vacacional == '01':
                date_start = contract.date_start
                if date_start:
                    d_from = fields.Date.from_string(date_from)
                    d_to = fields.Date.from_string(date_to)
                
                    date_start = fields.Date.from_string(date_start)
                    if datetime.datetime.today().year > date_start.year:
                        d_from = d_from.replace(date_start.year)
                        if str(d_to.day) == '29' and str(d_to.month) == '2':
                            d_to -=  datetime.timedelta(days=1)
                        d_to = d_to.replace(date_start.year)
                        
                        if d_from <= date_start <= d_to:
                            diff_date = day_to - datetime.datetime.combine(contract.date_start, datetime.time.max)
                            years = diff_date.days /365.0
                            antiguedad_anos = int(years)
                            tabla_antiguedades = contract.tablas_cfdi_id.tabla_antiguedades.filtered(lambda x: x.antiguedad <= antiguedad_anos)
                            tabla_antiguedades = tabla_antiguedades.sorted(lambda x:x.antiguedad, reverse=True)
                            vacaciones = tabla_antiguedades and tabla_antiguedades[0].vacaciones or 0
                            prima_vac = tabla_antiguedades and tabla_antiguedades[0].prima_vac or 0
                            attendances = {
                                 'name': 'Prima vacacional',
                                 'sequence': 2,
                                 'code': 'PVC',
                                 'number_of_days': vacaciones * prima_vac / 100.0, #work_data['days'],
                                 #'number_of_hours': 1['hours'],
                                 'contract_id': contract.id,
                            }
                            res.append(attendances)

            # compute Prima vacacional
            if contract.tipo_prima_vacacional == '03':
                date_start = contract.date_start
                if date_start:
                    d_from = fields.Date.from_string(date_from)
                    d_to = fields.Date.from_string(date_to)
                    
                    date_start = fields.Date.from_string(date_start)
                    if datetime.datetime.today().year > date_start.year and d_from.day > 15:
                        d_from = d_from.replace(date_start.year)
                        d_from = d_from.replace(day=1)
                        if str(d_to.day) == '29' and str(d_to.month) == '2':
                            d_to -=  datetime.timedelta(days=1)
                        d_to = d_to.replace(date_start.year)
                        
                        if d_from <= date_start <= d_to:
                            diff_date = day_to - datetime.datetime.combine(contract.date_start, datetime.time.max)
                            years = diff_date.days /365.0
                            antiguedad_anos = int(years)
                            tabla_antiguedades = contract.tablas_cfdi_id.tabla_antiguedades.filtered(lambda x: x.antiguedad <= antiguedad_anos)
                            tabla_antiguedades = tabla_antiguedades.sorted(lambda x:x.antiguedad, reverse=True)
                            vacaciones = tabla_antiguedades and tabla_antiguedades[0].vacaciones or 0
                            prima_vac = tabla_antiguedades and tabla_antiguedades[0].prima_vac or 0
                            attendances = {
                                 'name': 'Prima vacacional',
                                 'sequence': 2,
                                 'code': 'PVC',
                                 'number_of_days': vacaciones * prima_vac / 100.0, #work_data['days'],
                                 #'number_of_hours': 1['hours'],
                                 'contract_id': contract.id,
                            }
                            res.append(attendances)

            # compute Prima dominical
            if contract.prima_dominical:
                domingos = 0
                d_from = fields.Date.from_string(date_from)
                d_to = fields.Date.from_string(date_to)
                for i in range((d_to - d_from).days + 1):
                    if (d_from + datetime.timedelta(days=i+1)).weekday() == 0:
                        domingos = domingos + 1
                attendances = {
                            'name': 'Prima dominical',
                            'sequence': 2,
                            'code': 'PDM',
                            'number_of_days': domingos, #work_data['days'],
                            #'number_of_hours': 1['hours'],
                            'contract_id': contract.id,
                     }
                res.append(attendances)

            # compute leave days
            leaves = {}
            leave_days = 0
            inc_days = 0
            vac_days = 0
            factor = 1
            proporcional = 0
            falta_days = 0
            #if contract.semana_inglesa:
            #    factor = 7.0/5.0
            #if contract.septimo_dia:
            #    factor = 1.0/6.0

            if contract.periodicidad_pago == '04':
                dias_pagar = 15.2083
                factor = 1.1667 #7.0192/6.0
            elif contract.periodicidad_pago == '02':
                dias_pagar = 7.0192
                factor = 1.1667
            else:
                dias_pagar = (date_to - date_from).days + 1

            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to, calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.name or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                #current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.datetime.combine(day, datetime.time.min)),
                    tz.localize(datetime.datetime.combine(day, datetime.time.max)),
                    compute_leaves=False,
                )
                if work_hours and contract.periodicidad_pago == '02':
                            if holiday.holiday_status_id.name == 'FJS' or holiday.holiday_status_id.name == 'FI' or holiday.holiday_status_id.name == 'FR' or holiday.holiday_status_id.name == 'FJC':
                                leave_days += (hours / work_hours)*factor
                                current_leave_struct['number_of_days'] += (hours / work_hours)*factor
                                if leave_days > dias_pagar:
                                    leave_days = dias_pagar
                                if current_leave_struct['number_of_days'] > dias_pagar:
                                    current_leave_struct['number_of_days'] = dias_pagar
                            elif holiday.holiday_status_id.name == 'VAC':
                                leave_days += (hours / work_hours) * 7.0192/7.0
                                current_leave_struct['number_of_days'] += (hours / work_hours) * 7.0192/7.0
                                if leave_days > dias_pagar:
                                    leave_days = dias_pagar
                                if current_leave_struct['number_of_days'] > dias_pagar:
                                    current_leave_struct['number_of_days'] = dias_pagar
                            else:
                                if holiday.holiday_status_id.name != 'DFES' and holiday.holiday_status_id.name != 'DFES_3':
                                    leave_days += hours / work_hours
                                current_leave_struct['number_of_days'] += hours / work_hours
                elif work_hours and contract.periodicidad_pago == '04':
                            if holiday.holiday_status_id.name == 'FJS' or holiday.holiday_status_id.name == 'FI' or holiday.holiday_status_id.name == 'FR' or holiday.holiday_status_id.name == 'FJC':
                                leave_days += (hours / work_hours)*factor
                                current_leave_struct['number_of_days'] += (hours / work_hours)*factor
                                if leave_days > dias_pagar:
                                    leave_days = dias_pagar
                                if current_leave_struct['number_of_days'] > dias_pagar:
                                    current_leave_struct['number_of_days'] = dias_pagar
                            elif holiday.holiday_status_id.name == 'VAC':
                                leave_days += (hours / work_hours)
                                current_leave_struct['number_of_days'] += (hours / work_hours)
                                if leave_days > dias_pagar:
                                    leave_days = dias_pagar
                                if current_leave_struct['number_of_days'] > dias_pagar:
                                    current_leave_struct['number_of_days'] = dias_pagar
                            else:
                                if holiday.holiday_status_id.name != 'DFES' and holiday.holiday_status_id.name != 'DFES_3':
                                    leave_days += hours / work_hours
                                current_leave_struct['number_of_days'] += hours / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from, day_to, calendar=contract.resource_calendar_id)
            number_of_days = 0

            # ajuste en caso de nuevo ingreso
            nvo_ingreso = False
            date_start_1 = contract.date_start
            d_from_1 = fields.Date.from_string(date_from)
            d_to_1 = fields.Date.from_string(date_to)
            if date_start_1 > d_from_1:
                work_data['days'] =  (date_to - date_start_1).days + 1
                nvo_ingreso = True

            #dias_a_pagar = contract.dias_pagar
            _logger.info('dias trabajados %s  dias incidencia %s', work_data['days'], leave_days)

            if work_data['days'] < 100:
            #periodo para nómina quincenal
               if contract.periodicidad_pago == '04':
                   if contract.tipo_pago == '01' and nb_of_days < 30:
                      total_days = work_data['days'] + leave_days
                      if total_days != 15 or leave_days != 0:
                         if leave_days == 0 and not nvo_ingreso:
                            number_of_days = 15
                         elif nvo_ingreso:
                            number_of_days = work_data['days'] - leave_days
                         else:
                            number_of_days = 15 - leave_days
                      else:
                         number_of_days = work_data['days']
                   elif contract.tipo_pago == '03' and nb_of_days < 30:
                      total_days = work_data['days'] + leave_days
                      if total_days != 15.2083 or leave_days != 0:
                         if leave_days == 0  and not nvo_ingreso:
                            number_of_days = 15.2083
                         elif nvo_ingreso:
                            number_of_days = work_data['days'] * 15.2083 / 15 - leave_days
                         else:
                            if leave_days >= 15:
                                number_of_days = 0
                            else:
                                number_of_days = 15.2083 - leave_days
                      else:
                         number_of_days = work_data['days'] * 15.2083 / 15
                   else:
                      dias_periodo = (date_to - date_from).days + 1
                      total_days = work_data['days'] + leave_days
                      if total_days != dias_periodo or leave_days != 0:
                         if leave_days == 0  and not nvo_ingreso:
                            number_of_days = dias_periodo
                         elif nvo_ingreso:
                            number_of_days = work_data['days'] - leave_days
                         else:
                            number_of_days = dias_periodo - leave_days
                      else:
                         number_of_days = work_data['days']
               #calculo para nóminas semanales
               elif contract.periodicidad_pago == '02' and nb_of_days < 30:
                   number_of_days = work_data['days']
                ##   if contract.septimo_dia: #falta proporcional por septimo día
                   total_days = work_data['days'] + leave_days
                   if total_days != 7.0192 or leave_days != 0:
                      if leave_days == 0  and not nvo_ingreso:
                         number_of_days = 7.0192
                      elif nvo_ingreso:
                         number_of_days = work_data['days'] * 7.0192 / 7 - leave_days
                      else:
                         if leave_days >= 7:
                            number_of_days = 0
                         else:
                            number_of_days = 7.0192 - leave_days
                   else:
                      number_of_days = work_data['days'] * 7.0192 / 7
               #calculo para nóminas mensuales
               elif contract.periodicidad_pago == '05':
                  if contract.tipo_pago == '01':
                      total_days = work_data['days'] + leave_days
                      if total_days != 30:
                         if leave_days == 0 and not nvo_ingreso:
                            number_of_days = 30
                         elif nvo_ingreso:
                            number_of_days = work_data['days'] - leave_days
                         else:
                            number_of_days = 30 - leave_days
                  elif contract.tipo_pago == '03':
                      total_days = work_data['days'] + leave_days
                      if total_days != 30.42:
                         if leave_days == 0  and not nvo_ingreso:
                            number_of_days = 30.42
                         elif nvo_ingreso:
                            number_of_days = work_data['days'] * 30.42 / 30 - leave_days
                         else:
                            number_of_days = 30.42 - leave_days
                      else:
                         number_of_days = work_data['days'] * 30.42 / 30
                  else:
                      dias_periodo = (datetime.datetime.strptime(date_to, "%Y-%m-%d") - datetime.datetime.strptime(date_from, "%Y-%m-%d")).days + 1
                      total_days = work_data['days'] + leave_days
                      if total_days != dias_periodo:
                         if leave_days == 0  and not nvo_ingreso:
                            number_of_days = dias_periodo
                         elif nvo_ingreso:
                            number_of_days = work_data['days'] - leave_days
                         else:
                            number_of_days = dias_periodo - leave_days
                      else:
                         number_of_days = work_data['days']
               else:
                  number_of_days = work_data['days']
            else:
               date_start = contract.date_start
               if date_start:
                   d_from = fields.Date.from_string(date_from)
                   d_to = fields.Date.from_string(date_to)
               if date_start > d_from:
                   number_of_days =  (date_to - date_start).days + 1 - leave_days
               else:
                   number_of_days =  (date_to - date_from).days + 1 - leave_days
            attendances = {
                'name': _("Días de trabajo"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': number_of_days, #work_data['days'],
                'number_of_hours': round(number_of_days*8,2), # work_data['hours'],
                'contract_id': contract.id,
            }

            res.append(attendances)

            #Compute horas extas
            horas = horas_obj.search([('employee_id','=',contract.employee_id.id),('fecha','>=',date_from), ('fecha', '<=', date_to),('state','=','done')])
            horas_by_tipo_de_horaextra = defaultdict(list)
            for h in horas:
                horas_by_tipo_de_horaextra[h.tipo_de_hora].append(h.horas)
            
            for tipo_de_hora, horas_set in horas_by_tipo_de_horaextra.items():
                work_code = tipo_de_hora_mapping.get(tipo_de_hora,'')
                number_of_days = len(horas_set)
                number_of_hours = sum(is_number(hs) for hs in horas_set)
                     
                attendances = {
                    'name': _("Horas extras"),
                    'sequence': 2,
                    'code': work_code,
                    'number_of_days': number_of_days, 
                    'number_of_hours': number_of_hours,
                    'contract_id': contract.id,
                }
                res.append(attendances)
                
            res.extend(leaves.values())
        
        return res
