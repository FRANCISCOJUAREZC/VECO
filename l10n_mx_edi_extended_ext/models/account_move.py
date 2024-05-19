# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.tools.sql import column_exists, create_column


class AccountMove(models.Model):
    _inherit = 'account.move'


