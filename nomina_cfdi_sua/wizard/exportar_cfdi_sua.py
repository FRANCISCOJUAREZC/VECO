
from odoo import models, fields, api
import base64
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class exportar_cfdi_sua(models.TransientModel):
    _name = 'exportar.cfdi.sua'
    
    start_date = fields.Date('Fecha inicio')
    end_date = fields.Date('Fecha fin')
    employee_id = fields.Many2one("hr.employee",'Empleado')
    file_content = fields.Binary("Archivo")
    tipo_exp_sua = fields.Selection(
        selection=[('0', 'Ausentismo'),
                   ('1', 'Incapacidad'),
                   ('2', 'Alta / Reingreso'),
                   ('3', 'Baja'),
                   ('4', 'Cambio sueldo'),],
        string='Tipo exportación',
    )
    
    @api.multi
    def print_exportar_cfdi_sua(self):
        file_text = []
        is_idse = self._context.get('idse')
        
        domain = [('fecha','>=',self.start_date),('fecha','<=',self.end_date)]
        domain2 = [('fecha_inicio','>=',self.start_date),('fecha_inicio','<=',self.end_date)]
        if self.employee_id:
            domain.append(('employee_id','=', self.employee_id.id))
            domain2.append(('employee_id','=', self.employee_id.id))
        ################ EXPORTACIÓN A IDSE #############################
        if is_idse:
            domain.append(('tipo_de_incidencia', '!=','Cambio reg. patronal'))
            f_nomina = []
            in_nomina = []
        ################ EXPORTACIÓN A SUA #############################
        else:
            f_nomina = self.env['faltas.nomina'].search(domain2)
            in_nomina = self.env['incapacidades.nomina'].search(domain)
        i_nomina = self.env['incidencias.nomina'].search(domain)

        ################ EXPORTACIÓN A IDSE #############################
        if is_idse:
            for rec in i_nomina:
                employee = rec.employee_id
                data1 = employee.registro_patronal or ''
                longitudRP = len(employee.registro_patronal)
                data2 = employee.registro_patronal[longitudRP-1]
                data3= employee.segurosocial or ''
                longitudSS = len(employee.segurosocial)
                data4 = employee.segurosocial[longitudSS-1]
                data5 = employee.apellido_Paterno or ''
                data6 = employee.apellido_Materno or ''
                data7 = employee.nombreEmpleado or ''
                data8 = str(int(employee.contract_id.sueldo_base_cotizacion)) or ''
                data9 = ''
                data10 = employee.tipoDeTrabajador or ''
                data11 = employee.tipoDeSalario or ''
                data12 = employee.tipoDeJornada or ''
                data13 = employee.contract_id.date_start.strftime("%d%m%Y")
                data14 = employee.unidadMedicina or ''
                data15 = ''
                data16 = ''
                data17 = employee.no_guia or ''
                data18 = employee.no_empleado or ''
                data19 = ''
                data20 = employee.curp
                longitudCurp = len(employee.curp)
                data21 = employee.curp[longitudCurp-9]
                tipoMovimiento = ''
                causaDeBaja = ''
                #INDICATES THE MOVEMENT TYPE OF THE INCIDENCIA
                if rec.tipo_de_incidencia=='Reingreso':
                    tipoMovimiento = '08'
                    file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data6)+(data7)+(data8)+(" ")+(data10)
                    +(data11)+(data12)+(data13)+(data14)+("  ")+(tipoMovimiento)+(data17)+(data18)+(" ")+(data20)+(data21))
                if rec.tipo_de_incidencia=='Cambio salario':  
                    tipoMovimiento = '07'
                    file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data6)+(data7)+(data8)+("      ")+(" ")
                    +(data11)+(data12)+(data13)+("     ")+(tipoMovimiento)+(data17)+(data18)+(" ")+(data20)+(data21))
                if rec.tipo_de_incidencia=='Baja':
                    tipoMovimiento = '02'
                    file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data6)+(data7)+("               ")
                        +(data13)+("     ")+(data16)+(data17)+(data18)+(causaDeBaja)+("                  ")+(data21))
                
                #if employee.contract_id:
                #    data7='000'+str(int(employee.contract_id.sueldo_diario_integrado*100)) 
                #file_text.append((employee.registro_patronal or '')+(employee.segurosocial or '')+(data3)+(data4)+(data6)
                #    +(employee.apellido_Paterno)+(employee.apellido_Materno)+(employee.nombreEmpleado)+(str(int(employee.contract_id.sueldo_base_cotizacion)))
                #    +strftime(employee.contract_id.date_start).strftime("%d%m%Y")+(data5))
                
                #REINGRESO
                
                
                #CAMBIO SALARIO
               
                
                #BAJA
                               


               
                 

                #PRINT THE TEXT FILE FOR REINGRESOS        
                #file_text.append((data1)+(data2)+(data3)+(data4)+(data5)+(data6)+(data7)+(data8)+(data9)+(data10)
                #    +(data11)+(data12)+(data13)+(data14)+(data15)+(tipoMovimiento)+(data17)+(data18)+(data19)+(data20)+(data21))
        ################ EXPORTACIÓN A SUA #############################
        else:
            if self.tipo_exp_sua == '0': ##Tipo ausentismo
               for rec in f_nomina:
                   if rec.tipo_de_falta != 'Justificada con goce de sueldo':
                      employee = rec.employee_id
                      data3 = '11'
                      data4=''
                      if rec.fecha_inicio:
                          data4 = rec.fecha.strftime("%d%m%Y")   
                      data7 = ''
                      folioimss = '        '
                      #if employee.contract_id:
                      data7='0000000' #'{:07d}'.format(int(employee.contract_id.sueldo_diario_integrado*100))
                      file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '           ')+(data3)+(data4)+(folioimss)+'{:02d}'.format(rec.dias)+data7)

            if self.tipo_exp_sua == '1': ##Tipo Incapacidad
               for rec in in_nomina:
                   employee = rec.employee_id
                   data3 = '12'
                   data4=''

                   if rec.fecha:
                       data4 = rec.fecha.strftime("%d%m%Y")
                   data7 = ''
                   #if employee.contract_id:
                   data7='0000000' #'{:07d}'.format(int(employee.contract_id.sueldo_diario_integrado*100)) 
                   file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '')+(data3)+(data4)+(rec.folio_incapacidad[0:8])+'{:02d}'.format(rec.dias)+data7)

            if self.tipo_exp_sua == '2':  ##Tipo reingreso
               for rec in i_nomina:
                   if rec.tipo_de_incidencia=='Reingreso' or rec.tipo_de_incidencia=='Alta':
                      employee = rec.employee_id
                      data3 = '08'
                      data4=''
                      if rec.fecha:
                          data4 = rec.fecha.strftime("%d%m%Y")
                      data7 = '0000000'
                      folioimss = '        '
                      diasincidencia = '00'
                      if employee.contract_id:
                          data7='{:07d}'.format(int(round(employee.contract_id.sueldo_diario_integrado,2)*100))
                      file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '           ')+(data3)+(data4)+(folioimss)+(diasincidencia)+data7)

            if self.tipo_exp_sua == '3':  ##Tipo baja
               for rec in i_nomina:
                   if rec.tipo_de_incidencia=='Baja':
                      employee = rec.employee_id
                      data3 = '02'
                      data4=''
                      if rec.fecha:
                          data4 = rec.fecha.strftime("%d%m%Y")
                      data7 = '0000000'
                      folioimss = '        '
                      diasincidencia = '00'
                      file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '           ')+(data3)+(data4)+(folioimss)+(diasincidencia)+data7)

            if self.tipo_exp_sua == '4':  ##Tipo cambio de sueldo
               for rec in i_nomina:
                   if rec.tipo_de_incidencia=='Cambio salario':
                      employee = rec.employee_id
                      data3 = '07'
                      data4=''
                      if rec.fecha:
                          data4 = rec.fecha.strftime("%d%m%Y")
                      data7 = '0000000'
                      folioimss = '        '
                      diasincidencia = '00'
                      if employee.contract_id:
                          data7='{:07d}'.format(int(round(employee.contract_id.sueldo_diario_integrado,2)*100))
                      file_text.append((employee.registro_patronal[0:11] or '           ')+(employee.segurosocial[0:11] or '           ')+(data3)+(data4)+(folioimss)+(diasincidencia)+data7)

        if not file_text:
            raise Warning("No hay datos para generar el archivo.")
        
        file_text = '\n'.join(file_text)
        file_text = file_text.encode()
        filename = datetime.now().strftime("%y%m-%d%H%M%S")+'.txt'
        self.write({'file_content':base64.b64encode(file_text)})
        return {
                'type' : 'ir.actions.act_url',
                'url': "/web/content/?model="+self._name+"&id=" + str(self.id) + "&field=file_content&download=true&filename="+filename+'&mimetype=text/plain',
                'target':'self',
                }
        