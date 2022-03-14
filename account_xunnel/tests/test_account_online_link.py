from . import response

from json import dumps
from unittest.mock import Mock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from requests_mock import mock

requests = Mock()


class TestAccountOnlineLink(TransactionCase):

    def setUp(self):
        super().setUp()
        self.url = "https://xunnel.com/"
        self.company = self.env.user.company_id
        self.company.xunnel_token = 'test token'
        self.link = self.env['account.online.link'].create({
            "name": 'Acme Bank - Normal with Attachments',
            'is_xunnel': True,
            "client_id": '5ad5ad730c212a6a268b45e4',
            "company_id": self.env.user.company_id.id,
        })

    def test_01_update_credentials(self):
        with self.assertRaises(UserError):
            self.link.update_credentials()

    @patch('odoo.addons.account_online_synchronization.models.account_online.AccountOnlineLink._fetch_odoo_fin')
    def test_02_fetch_odoo_fin(self, _fetch_odoo_fin):
        self.link._fetch_odoo_fin(url='test')
        _fetch_odoo_fin.assert_called_once()

    @mock()
    def test_03_get_journals(self, request=None):
        request.post('%sget_xunnel_journals' % self.url, text=dumps(dict(response.ERROR)))
        with self.assertRaises(UserError):
            self.link._get_journals()
