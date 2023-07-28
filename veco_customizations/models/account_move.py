# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    line_ids = fields.One2many(states={}, readonly=False)
