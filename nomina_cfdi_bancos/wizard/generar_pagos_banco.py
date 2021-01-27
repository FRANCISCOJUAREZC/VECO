# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime, date
import base64
import logging
_logger = logging.getLogger(__name__)

class GenerarPagosBanco(models.TransientModel):
    _name='generar.pagos.banco'
    _description = 'GenerarPagosBanco'

    #banco_id = fields.Many2one("res.bank",string='Banco')
    banco_rfc = fields.Selection(
        selection=[('BBA830831LJ2', 'BBVA Bancomer - Cuentas distintos bancos'),
                   ('BBA830831LJ2_2', 'BBVA Bancomer - Solo cuentas de banco BBVA'),
                   ('BMN930209927', 'Banorte'),
                    ('BSM970519DU8', 'Santander - Solo cuentas de banco Santanter'),
                    ('BSM970519DU8_2', 'Santander - Cuentas distintos bancos'),
                    ('BBA940707IE1', 'Banco del Bajío'),
                    ('BNM840515VB1', 'Banamex'),],
        string=_('Banco de dispersión'),
    )
    dato1 = fields.Char("Código de pago")
    dato2 = fields.Char("Dato adicional 2")
    dato3 = fields.Char("Dato adicional 3")
    file_content = fields.Binary("Archivo")
    diario_pago = fields.Many2one('account.journal', string='Cuenta de pago', domain=[('type', '=', 'bank')])
    fecha_dispersion = fields.Date("Fecha de dispersión")

    @api.multi
    def action_print_generar_pagos(self):
        file_text = []
        ctx = self._context.copy()
        active_id = ctx.get('active_id')
        active_model = ctx.get('active_model')
        str_encabezado = []
        str_sumario = []
        num_registro = 1
        num_empleados = 0
        monto_total = 0
        if active_id and active_model=='hr.payslip.run':
            record = self.env[active_model].browse(active_id)

           # if self.diario_pago.bank_id.bic == 'BBA830831LJ2' or self.diario_pago.bank_id.bic == 'BSM970519DU8' or self.diario_pago.bank_id.bic == 'BMN930209927' or self.diario_pago.bank_id.bic == 'BNM840515VB1':
            #   self.banco_rfc = self.diario_pago.bank_id.bic

              ##################################################################################
              ###################################################################################
              #encabezados 
              ###################################################################################
              ###################################################################################
            if self.banco_rfc == 'BBA830831LJ2': # Bancomer
                  data1 = '3' 
                  data2 = '40'
                  data5 = '00' # estado pago
                  data7 = '          ' # filler
            elif self.banco_rfc == 'BSM970519DU8' or self.banco_rfc == 'BSM970519DU8_2':            # Santander
                  enc1 = '1'+ str(num_registro).rjust(5, '0') + 'E'
                  enc2 = datetime.now().strftime("%m%d%Y")
                  if self.diario_pago.bank_account_id.acc_number:
                     enc3 = self.diario_pago.bank_account_id.acc_number.ljust(16)
                  else:
                     enc3 = '                '
                  enc4 = self.fecha_dispersion.strftime("%m%d%Y")
                  str_encabezado.append((enc1)+(enc2)+(enc3)+(enc4))
                  num_registro += 1

              ##################################################################################
              ###################################################################################
              #registos de detalle
              ###################################################################################
              ###################################################################################
            for payslip in record.slip_ids.filtered(lambda x: x.state!='cancel'):
                    employee = payslip.employee_id

                    if employee.tipo_pago=='transferencia' and employee.diario_pago.bank_id.bic == str(self.banco_rfc).replace('_2',''):
                        net_total = sum(payslip.line_ids.filtered(lambda x:x.code=='EFECT').mapped('total'))
                        _logger.info('empleado %s --- banco %s', employee.name, self.banco_rfc)
                        if self.banco_rfc == 'BBA830831LJ2': # Dispersión de Bancomer
                           data1 = '3'+ employee.rfc # no identificador y rfc
                           if employee.tipo_cuenta == 't_debido':      #Tipo - cuenta
                              data2 = '03'
                           elif employee.tipo_cuenta == 'cheque':
                              data2 = '01'
                           else:
                              data2 = '40'
                           if employee.no_cuenta:    #Banco - Plaza destino - No. cuenta
                               data3 = employee.no_cuenta[0:6] + '0000' + employee.no_cuenta[6:]
                           data4 = str(round(net_total,2)).replace('.','').rjust(15, '0') # monto total
                           data5 = '00' # estado pago
                           data6 = employee.name[0:40].ljust(40, ' ') # nombre del empleado
                           data7 = '          ' # fillers
                           file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data6)+(data7))
                        elif self.banco_rfc == 'BBA830831LJ2_2': # Dispersión de Bancomer solo cuentas BBVA
                           data1 = str(num_registro).zfill(9) # número consecutivo del registro
                           data2 = employee.rfc and employee.rfc.ljust(16)[:16] or '                '  #rfc 
                           data3 = '99' # NOMINA
                           data4 = employee.no_cuenta.ljust(20) #NUMERO DE CUENTA 10 DIGITOS BANCOMER
                           data5 =  str(round(net_total,2)).split('.')[0].rjust(13, '0')
                           if net_total > 0:
                              data5b =  str(round(net_total,2)).split('.')[1].ljust(2, '0')
                           else:
                              data5b =  '00'
                           nombre_empleado = employee.name.replace('/','').replace('-','').replace('.','').replace(':','').replace('?','').replace('&','').replace('!','')
                           nombre_empleado = nombre_empleado.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
                           nombre_empleado = nombre_empleado.replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U')
                           nombre_empleado = nombre_empleado.replace('ñ','n').replace('Ñ','N')
                           data6 = nombre_empleado[0:40].ljust(40, ' ') # nombre del empleado
                           data7 = '001' # fillers
                           data8 = '001' # fillers
                           file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data5b)+(data6)+(data7)+(data8)+'\r')
                           num_registro += 1
                        elif self.banco_rfc == 'BSM970519DU8': # Dispersión de Santander - solo cuentas santander
                           data1 = '2'
                           data2 = str(num_registro).zfill(5)
                           data3 = str(employee.no_empleado).ljust(7)
                           data4 = employee.dispersion_paterno.ljust(30)[:30]
                           data5 = employee.dispersion_materno.ljust(20)[:20]
                           data6 = employee.dispersion_nombre.ljust(30)[:30]
                           data7 = employee.no_cuenta.ljust(16)
                           data8 = str(round(net_total,2)).split('.')[0].rjust(16, '0')
                           if net_total > 0:
                              data8b =  str(round(net_total,2)).split('.')[1].ljust(2, '0')
                           else:
                              data8b =  '00'
                           #for var in data8b:
                           #   _logger.info('total %s', var)
                           data9 = self.dato1 or '' #'01'
                           file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data6)+(data7)+(data8)+(data8b)+(data9))
                           num_registro += 1
                        elif self.banco_rfc == 'BSM970519DU8_2': # Dispersión de Santander - distintos bancos
                           data1 = '2'
                           data2 = str(num_registro).zfill(5)
                           data3 = employee.name[0:50].ljust(50, ' ')
                           if employee.tipo_cuenta == 't_debido':
                              data4 = '02'
                           elif employee.tipo_cuenta == 'cheques':
                              data4 = '01'
                           elif employee.tipo_cuenta == 'c_ahorro':
                              data4 = '40'
                           data5 = employee.no_cuenta.ljust(20)
                           data6 = str(round(net_total,2)).replace('.','').rjust(18, '0')
                           data7 = employee.clave_santander_banco and employee.clave_santander_banco.rjust(5, '0') or '00000'
                           data8 = employee.plaza_santander_banco and employee.plaza_santander_banco.rjust(5, '0') or '00000'
                          # data9 = self.dato1
                           file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data6)+(data7)+(data8))
                           num_registro += 1

                        num_empleados += 1
                        monto_total += round(net_total,2)

              ##################################################################################
              ###################################################################################
              #sumario
              ###################################################################################
              ###################################################################################
            if self.banco_rfc == 'BBA830831LJ2': # Bancomer
                   data1 = '3' # no identificador y rfc
                   data2 = '40'
                   data5 = '00' # estado pago
                   data7 = '          ' # filler
            elif self.banco_rfc == 'BSM970519DU8' or self.banco_rfc == 'BSM970519DU8_2':            # Santander
                   sum1 = '3'
                   sum2 = str(num_registro).rjust(5, '0')
                   sum3 = str(num_empleados).rjust(5, '0')
                   #sum4 = str(round(monto_total,2)).replace('.','').rjust(18, '0')
                   sum4 = str(round(monto_total,2)).split('.')[0].rjust(16, '0')
                   if monto_total > 0:
                      sum5 =  str(round(monto_total,2)).split('.')[1].ljust(2, '0')
                   else:
                      sum5 =  '00'
                   str_sumario.append((sum1)+(sum2)+(sum3)+(sum4)+(sum5))

#            else:
#               raise Warning("Banco no compatible con la dispersión.")
        if not file_text:
            raise Warning("No hay información para generar el archivo de dispersión.")
        file_text = str_encabezado + file_text + str_sumario
        file_text = '\n'.join(file_text)
        file_text = file_text.encode()
        filename = datetime.now().strftime("%y%m-%d%H%M%S")+'.txt'
        self.write({'file_content':base64.b64encode(file_text)})
        return {
                'type' : 'ir.actions.act_url',
                'url': "/web/content/?model="+self._name+"&id=" + str(self.id) + "&field=file_content&download=true&filename="+filename+'&mimetype=text/plain',
                'target':'self',
                }
