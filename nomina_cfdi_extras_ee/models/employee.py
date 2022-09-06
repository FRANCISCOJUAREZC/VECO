# -*- coding: utf-8 -*-
from odoo import fields, models

class Employee(models.Model):
    _inherit = 'hr.employee'

    no_employee = fields.Char('No de empleado')

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    no_employee = fields.Char('No de empleado')
