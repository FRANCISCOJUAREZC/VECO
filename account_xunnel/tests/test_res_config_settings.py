import os
from odoo.tools import misc
from . import response

from json import dumps, loads
from unittest.mock import Mock

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from requests_mock import mock

requests = Mock()


class TestResConfigSettings(TransactionCase):

    def setUp(self):
        super().setUp()
        self.url = "https://xunnel.com/"
        self.company = self.env.user.company_id
        self.config_settings = self.env['res.config.settings'].create({})

    def test_01_create(self):
        vals_1 = {
            'xunnel_token': 'test token from vals',
        }
        config_settings_1 = self.config_settings.create(vals_1)
        self.assertEqual(config_settings_1.xunnel_token, 'test token from vals')
        vals_2 = ({})
        self.config_settings.xunnel_token = 'test token'
        config_settings_2 = self.config_settings.create(vals_2)
        self.assertEqual(config_settings_2.xunnel_token, 'test token')

    @mock()
    def test_02_sync_xunnel_providers(self, request=None):
        self.config_settings.xunnel_token = False
        with self.assertRaises(UserError):
            self.config_settings.sync_xunnel_providers()

        def _response(request, context):
            data = loads(request.text)
            path = 'response_journal_%s.json'
            if data.get('account_identifier') == '5ad79e9d0b212a5b608b459a':
                return misc.file_open(os.path.join(
                    'account_xunnel', 'tests', path % '2')).read()
            return misc.file_open(
                os.path.join('account_xunnel', 'tests', path % '1')).read()

        request.post('%sget_xunnel_providers' % self.url, text=dumps(dict(response=response.PROVIDERS)))
        request.post('%sget_xunnel_journals' % self.url, text=_response)

        self.config_settings.xunnel_token = 'test token'

        expected_res = {
            'type': 'ir.actions.client',
            'tag': 'account_xunnel.synchronized_accounts',
            'name': 'Xunnel response.',
            'target': 'new',
            'params': {
                'message': 'Success! 2 banks have been synchronized.',
                'message_class': 'success'}
        }

        res = self.config_settings.sync_xunnel_providers()
        self.assertEqual(res, expected_res)
