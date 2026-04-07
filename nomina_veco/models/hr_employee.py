# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class Contract(models.Model):
    _inherit = "hr.employee"

    retencion_judicial = fields.Boolean('Retención Judicial')
    retencion_judicial_amount = fields.Float('Monto Retención Judicial')
