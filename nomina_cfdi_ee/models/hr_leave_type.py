# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    code = fields.Char('Código')

