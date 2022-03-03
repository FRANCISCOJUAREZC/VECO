# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        help='''If set, this budget line will take in care
         the partner on the analytic lines to achievement computation.'''
    )

    def _compute_practical_amount(self):
        """Method overriden in order to compute the practical amount
        filtered by the base filter adding the partner field"""
        for line in self:
            acc_ids = line.general_budget_id.account_ids.ids
            partner_id = line.partner_id.id
            date_to = line.date_to
            date_from = line.date_from
            if line.analytic_account_id.id:
                analytic_line_obj = self.env['account.analytic.line']
                domain = [('account_id', '=', line.analytic_account_id.id),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ]
                if acc_ids:
                    domain += [('general_account_id', 'in', acc_ids)]
                if partner_id:
                    domain += [('partner_id', '=', line.partner_id.id)]

                where_query = analytic_line_obj._where_calc(domain)
                analytic_line_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = (
                    where_query.get_sql())
                select = (
                    "SELECT SUM(amount) FROM " + from_clause + " WHERE " +
                    where_clause
                )

            else:
                aml_obj = self.env['account.move.line']
                domain = [('account_id', 'in',
                           line.general_budget_id.account_ids.ids),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ('move_id.state', '=', 'posted'),
                          ]
                if partner_id:
                    domain += [('partner_id', '=', line.partner_id.id)]
                where_query = aml_obj._where_calc(domain)
                aml_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = (
                    where_query.get_sql())
                select = (
                    "SELECT sum(credit)-sum(debit) FROM " +
                    from_clause + " WHERE " + where_clause)

            self.env.cr.execute(select, where_clause_params)
            line.practical_amount = self.env.cr.fetchone()[0] or 0.0

    def action_open_budget_entries(self):
        """Super method overriden in order to
        add the partner to the action domain"""
        action = super(
            CrossoveredBudgetLines, self).action_open_budget_entries()
        self.ensure_one()
        if self.partner_id:
            action['domain'].append(('partner_id', '=', self.partner_id.id))
        return action
