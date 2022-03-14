# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
from json import dumps

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import misc
from requests_mock import mock


class TestXunnelAccount(TransactionCase):

    def setUp(self):
        super().setUp()
        self.url = "https://xunnel.com/"
        self.company = self.env['res.company'].browse(self.ref('base.main_company'))
        self.company.xunnel_token = 'test'

    @mock()
    def test_01_sync_xunnel_documents(self, request=None):
        """Test requesting all transactions from an account and
        making a bank statement. Also checks last_sync's refreshed.
        """
        documents_response = misc.file_open(os.path.join(
            'invoice_xunnel', 'tests', 'response_documents.json')).read()
        request.post('%sget_invoices_sat' % self.url, text=documents_response)
        old_sync = fields.Date.to_date('2018-01-01')
        self.company.xunnel_last_sync = old_sync
        self.company._sync_xunnel_documents()
        last_sync = self.company.xunnel_last_sync
        self.assertTrue(old_sync < last_sync)
        self.company.vat = False

    @mock()
    def test_02_sync_xunnel_documents(self, request):
        """Test a bad requesting transactions. Also checks
        last_sync is not refreshed. Six documents are returned
        but 3 of those are already in the database and must not be overwritten.
        """
        request.post(
            '%sget_invoices_sat' % self.url,
            text=dumps({"error": "Expected error for testing"}))

        documents = self.env['documents.document']
        inital_documents = documents.search_count([])
        old_sync = '1970-01-01'
        self.company.xunnel_last_sync = old_sync
        with self.assertRaisesRegex(UserError, 'Expected error for testing'):
            self.company._sync_xunnel_documents()
            final_documents = documents.search_count([])
            self.assertEquals(final_documents - inital_documents, 3)
        self.assertEqual(old_sync, fields.Date.to_string(self.company.xunnel_last_sync))
