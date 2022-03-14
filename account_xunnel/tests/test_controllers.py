from unittest.mock import patch

from odoo.tests.common import HttpCase
from odoo.tools import config

HOST = '127.0.0.1'
PORT = config['http_port']


class TestController(HttpCase):

    def setUp(self):
        super().setUp()
        self.url_webhook_handler = '/account_xunnel/xunnel_webhook_connection'
        self.company = self.env.user.company_id
        self.company.xunnel_token = 'test token'

    def url_open(self, url, data=None, timeout=10, json=None):
        """Makes possible to test JSON-based controllers
        """
        if json is None:
            return super().url_open(url, data, timeout)
        if url.startswith('/'):
            url = "http://%s:%s%s" % (HOST, PORT, url)
        return self.opener.post(url, json=json, timeout=timeout)

    @patch('odoo.addons.account_xunnel.models.res_company.ResCompany._sync_xunnel_providers')
    def test_01_webhook_hanlder(self, _sync_xunnel_providers):
        json = {
            'provider': 'test',
            'handle': 'test',
            'data': 'test',
        }
        self.url_open(self.url_webhook_handler, json=json)
        _sync_xunnel_providers.assert_called_once()

    @patch('odoo.addons.account_xunnel.models.account_online_account.AccountOnlineAccount._retrieve_transactions')
    def test_02_webhook_hanlder(self, _retrieve_transactions):
        journal = self.env['account.online.account'].create({})
        journal.online_identifier = journal.id
        json = {
            'provider': 'test',
            'handle': 'refresh',
            'data': 'test',
            'sync_data': {
                'journal': {
                    'journal': journal.id,
                    },
            }
        }
        self.url_open(self.url_webhook_handler, json=json)
        _retrieve_transactions.assert_called_once()
