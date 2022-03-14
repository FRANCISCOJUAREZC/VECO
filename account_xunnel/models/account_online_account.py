# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from datetime import datetime
from time import mktime

from odoo import _, models
from odoo.exceptions import UserError


class AccountOnlineAccount(models.Model):
    _inherit = 'account.online.account'

    def _retrieve_transactions(self, forced_params=None):
        self.ensure_one()
        if not self.account_online_link_id.is_xunnel:
            return super()._retrieve_transactions()
        resp_json = self._get_transactions(forced_params)
        transactions = self._prepare_transactions(resp_json)
        if not transactions:
            return 0
        response = self._process_transactions(transactions)
        return response

    def _get_transactions(self, forced_params):
        params = {
            'id_account': self.online_identifier,
            'id_credential': self.account_online_link_id.client_id
        }
        if forced_params is not None:
            params.update(forced_params)
        elif self.last_sync:
            params.update(dt_transaction_from=mktime(self.last_sync.timetuple()))
        resp = self.env.company._xunnel('get_xunnel_transactions', params)
        err = resp.get('error')
        if err:
            raise UserError(err)
        return json.loads(resp.get('response'))

    def _prepare_transactions(self, resp_json):
        json_transactions = resp_json['transactions']
        if not self.journal_ids or not json_transactions:
            return False
        journal = self.journal_ids[0]
        transactions = {}
        for transaction in json_transactions:
            date = datetime.strptime(transaction['dt_authorization'], '%Y-%m-%d')
            trans = {
                'ref': transaction['reference'],
                'payment_ref': transaction['reference'],
                'online_transaction_identifier': transaction['id_transaction'],
                'date': date.date(),
                'amount': transaction['amount'],
                'card_number': transaction['card_number'],
            }
            manual_lines = self.env['account.bank.statement.line'].search([
                ('journal_id', '=', journal.id),
                ('date', '=', trans['date']),
                ('amount', '=', trans['amount']),
                ('online_transaction_identifier', '=', False)], limit=2)
            if len(manual_lines) == 1:
                manual_lines.online_transaction_identifier = trans['online_transaction_identifier']
                manual_lines.name += ' - ' + trans['payment_ref']
                continue
            if 'meta' in transaction and 'location' in transaction['meta']:
                trans['location'] = transaction['meta']['location']
            if journal.bank_statement_creation_groupby == 'day':
                transactions.setdefault(transaction['dt_authorization'], []).append(trans)
            elif journal.bank_statement_creation_groupby == 'week':
                week = date.isocalendar()[1]
                transactions.setdefault(week, []).append(trans)
            elif journal.bank_statement_creation_groupby == 'bimonthly':
                if date.day > 15:
                    transactions.setdefault(date.strftime('%Y-%m-15'), []).append(trans)
                else:
                    transactions.setdefault(date.strftime('%Y-%m-01'), []).append(trans)
            elif journal.bank_statement_creation_groupby == 'month':
                transactions.setdefault(date.strftime('%Y-%m'), []).append(trans)
            else:
                transactions.setdefault('transactions', []).append(trans)
        return transactions

    def _process_transactions(self, transactions):
        journal = self.journal_ids[0]
        statement_obj = self.env['account.bank.statement']
        line_statement_obj = self.env['account.bank.statement.line']
        response = 0
        last_date = None
        for __, trans in sorted(transactions.items()):
            response += len(statement_obj._online_sync_bank_statement(trans, self))
            statement = statement_obj.search([('journal_id', '=', journal.id)], order="id desc", limit=1)
            starting_balance = line_statement_obj.search([
                ('statement_id', '=', statement.id),
                ('online_transaction_identifier', '=', False),
                ('payment_ref', '=', _(
                    'Opening statement: first synchronization')),
                ], limit=1)
            if starting_balance:
                statement.write({'balance_start': starting_balance.amount})
                starting_balance.unlink()
                response -= 1
            last_date = line_statement_obj.search(
                [('statement_id', '=', statement.id)], limit=1,
                order='date desc').date
            statement.date = last_date
            statement.line_ids.filtered('online_transaction_identifier').write(
                {'narration': _('Transaction synchronized from Xunnel')})
        if last_date:
            self.last_sync = last_date
        return response
