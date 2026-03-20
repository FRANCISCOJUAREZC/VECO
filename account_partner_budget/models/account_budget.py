# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class BudgetLine(models.Model):
    _inherit = "budget.line"

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        help='''If set, this budget line will take in care
         the partner on the analytic lines to achievement computation.''',
    )

    def _compute_all(self):
        if self.partner_id:
            grouped = {
                line: (committed, achieved)
                for line, committed, achieved in self.env['budget.report']._read_group(
                    domain=[('budget_line_id', 'in', self.ids), ('budget_line_id.partner_id', '=', self.partner_id.id)],
                    groupby=['budget_line_id'],
                    aggregates=['committed:sum', 'achieved:sum'],
                )
            }
        else:
            grouped = {
                line: (committed, achieved)
                for line, committed, achieved in self.env['budget.report']._read_group(
                    domain=[('budget_line_id', 'in', self.ids)],
                    groupby=['budget_line_id'],
                    aggregates=['committed:sum', 'achieved:sum'],
                )
            }
        for line in self:
            committed, achieved = grouped.get(line, (0, 0))
            line.committed_amount = committed
            line.achieved_amount = achieved
            line.committed_percentage = line.budget_amount and (line.committed_amount / line.budget_amount)
            line.achieved_percentage = line.budget_amount and (line.achieved_amount / line.budget_amount)

    def action_open_budget_entries(self):
        """Super method overriden in order to
        add the partner to the action domain"""
        action = super(
            BudgetLine, self).action_open_budget_entries()
        self.ensure_one()
        if self.partner_id:
            action['domain'].append(('partner_id', '=', self.partner_id.id))
        return action
