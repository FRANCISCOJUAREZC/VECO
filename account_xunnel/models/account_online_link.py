# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountOnlineLink(models.Model):
    _inherit = 'account.online.link'

    is_xunnel = fields.Boolean()

    def _fetch_odoo_fin(self, url, data=None, ignore_status=False):
        if not self.env.context.get('xunnel_operation'):
            return super()._fetch_odoo_fin(url, data=data, ignore_status=ignore_status)

        params = {
            'id_account': data['account_id'],
            'id_credential': self.client_id,
        }

        res = self.env.company._xunnel('get_xunnel_transactions', params)
        res = json.loads(res.get('response'))
        res['transactions'] = [
            {
                'online_transaction_identifier': transaction['id_transaction'],
                'amount': transaction['amount'],
                'date': datetime.strptime(transaction['dt_authorization'], '%Y-%m-%d'),
                'id': transaction['id_transaction'],
                'payment_ref': transaction['reference'],
            }
            for transaction in res['transactions']
        ]
        return res

    def sync_journals(self):
        """Get all journals and check them in the database
        to create them if they're not.
        """
        for journal in self._get_journals():
            online_account = self.env['account.online.account'].search(
                [('account_online_link_id', '=', self.id), ('online_identifier', '=', journal.get('id_account'))])
            vals = {
                'name': journal.get('name'),
                'balance': journal.get('balance'),
                'account_number': journal.get('number'),
                'online_identifier': journal.get('id_account'),
                'account_online_link_id': self.id
            }
            if online_account:
                online_account.write(vals)
            else:
                online_account.create(vals)

    def _get_journals(self):
        """Requests https://wwww.xunnel.com/ to retrive all journals
        related to the indicated provider.
        """
        res = self.company_id._xunnel(
            'get_xunnel_journals',
            dict(account_identifier=self.client_id))
        err = res.get('error')
        if err:
            raise UserError(err)
        return res.get('response')

    def update_credentials(self):
        raise UserError(_(
            'Updating credentials is not allowed here. '
            'Please go to https://www.xunnel.com/ to achieve that.'))

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

    def _open_iframe(self, mode='link'):
        if self.is_xunnel:
            self.xunnel_exception()
        return super()._open_iframe(mode)

    def _fetch_transactions(self, refresh=True, accounts=False):
        if self.is_xunnel:
            self.xunnel_exception()
        return super()._fetch_transactions(refresh, accounts)

    def xunnel_exception(self):
        raise UserError(_('''Xunnel bank: Unsupported operation.

Please check our documentation in: https://xunnel.com/en_US/user-manual'''))
