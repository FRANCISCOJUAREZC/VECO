# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    workforce_account_id = fields.Many2one(
        comodel_name='account.account',
    )
    workforce_account_ids = fields.One2many(
        comodel_name='workforce.account.line',
        inverse_name='warehouse_id',
        string="Workforce Account Breakdown",
    )
    workforce_cost_journal_id = fields.Many2one(
        comodel_name='account.journal',
    )

    @api.constrains('workforce_account_ids')
    def check_workforce_line_ids(self):
        for rec in self:
            if not rec.workforce_account_ids:
                continue
            total_percentage = sum(
                rec.mapped('workforce_account_ids.percentage'))
            if total_percentage != 100:
                raise ValidationError(
                    _('Error! the percentage total must be 100%.'))

            if self._check_workforce_lines():
                raise ValidationError(
                    _('Error! there are repeated account'
                        ' in the workforce distribution lines.'))

    @api.model
    def _check_workforce_lines(self):
        """ Returns True if there are the same account on different records"""
        seen = []
        for line in self.workforce_account_ids:
            if line.account_id in seen:
                return True
            seen.append(line.account_id)
        return False


class WorkForceAccountLine(models.Model):
    _name = 'workforce.account.line'
    _description = 'Workforce Account Line'

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string="Account",
    )
    percentage = fields.Float()
