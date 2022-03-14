# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _compute_has_synchronized_xunnel(self):
        for rec in self:
            statement = self.env['account.bank.statement'].search(
                [('journal_id', '=', rec.id)], order="date desc, id desc", limit=1)
            has_online_sync = statement and self.env['account.bank.statement.line'].search([
                ('statement_id', '=', statement.id),
                ('online_transaction_identifier', '!=', False)], limit=1)
            is_online_bank = rec.bank_statements_source == 'online_sync'
            rec.has_synchronized_xunnel = (is_online_bank and has_online_sync)

    has_synchronized_xunnel = fields.Boolean(
        help='Recognize if has synchronized with Xunnel',
        compute='_compute_has_synchronized_xunnel')
    online_journal_last_sync = fields.Date(
        "Online account last synchronization",
        related="account_online_account_id.last_sync",
        tracking=True)

    def manual_sync(self):
        online_account = self.env['account.online.account'].search([('journal_ids', 'in', self.ids)], limit=1)
        if not self.account_online_link_id.is_xunnel:
            return super().manual_sync()
        res = online_account.with_context(xunnel_operation=True)._retrieve_transactions()
        if res == 0:
            raise ValidationError(_("""No item was found in the period of time that you choose, please change the \
                                    Xunnel Synchronization Date of the journal or check if its associated  account \
                                    has transactions at www.xunnel.com"""))
        return res
