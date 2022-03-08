# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    mrp_timeline_id = fields.Many2one(
        comodel_name='mrp.workcenter.productivity',
        ondelete='cascade',
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    mrp_timeline_id = fields.Many2one(
        comodel_name='mrp.workcenter.productivity',
    )
