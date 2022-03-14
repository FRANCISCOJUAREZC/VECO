from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestWizardChangeDate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.user.company_id
        self.env.user.company_id.xunnel_token = 'test token'
        self.url = "https://xunnel.com/"

    def test_01_change_sync_date(self):
        """This tests has 4 cases.
        Case 1: An online journal without account_online_journal_id and bank_statement source
            is created, the result of calling change_sync_date() is a ValidationError
        Case 2: The same online journal is updated, add onli bank_statements_source value,
            the result of calling
            change_sync_date() is a ValidationError
        Case 3: The same online journal is updated, Credentials manager_online_journal_id and remove
            bank_statement source values, the result of calling change_sync_date() is a ValidationError
        Case 4: The same online journal is updated, add bank_statement source value, the result of calling
            change_sync_date() with sync_date = 2021-10-10 is that the online journal sync date is
            2021-10-10
        """
        journal = self.env['account.journal'].search([], limit=1)
        link_account = self.env['account.online.link'].create({'name': 'Test Bank'})
        online_journal = self.env['account.online.account'].create(
            {'name': 'MyBankAccount', 'account_online_link_id': link_account.id})
        journal.bank_statements_source = False

        wizard = self.env['wizard.change.date'].create({'sync_date': '2021-10-10'})
        with self.assertRaises(ValidationError):
            wizard.with_context(active_id=journal.id).change_sync_date()

        journal.bank_statements_source = 'online_sync'
        with self.assertRaises(ValidationError):
            wizard.with_context(active_id=journal.id).change_sync_date()

        online_journal.update({'journal_ids': [(6, 0, [journal.id])]})
        journal.account_online_account_id = online_journal.id
        journal.bank_statements_source = False
        with self.assertRaises(ValidationError):
            wizard.with_context(active_id=journal.id).change_sync_date()

        journal.bank_statements_source = 'online_sync'
        wizard.with_context(active_id=journal.id).change_sync_date()
        self.assertEqual(str(online_journal.last_sync), '2021-10-10')
