import base64

from odoo.tests.common import TransactionCase

TEXT_datas = base64.b64encode(bytes("Test", 'utf-8'))


class TestDocumentsWorkflowRule(TransactionCase):

    def setUp(self):
        super().setUp()
        self.folder_a = self.env['documents.folder'].create({
            'name': 'folder A',
        })
        self.document = self.env['documents.document'].create({
            'datas': TEXT_datas,
            'name': 'file.txt',
            'mimetype': 'text/plain',
            'folder_id': self.folder_a.id,
            'xunnel_document': False,
        })

    def test_01_create_record(self):
        documents_workflow = self.env['documents.workflow.rule'].create({
            'domain_folder_id': self.folder_a.id,
            'name': 'test',
        })

        documents_workflow.create_model = 'xunnel.invoice'
        res_1 = documents_workflow.create_record(self.document)
        expected_res_1 = {
            'type': 'ir.actions.act_window',
            'res_model': 'attach.xmls.wizard',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'file_names': '[{"name": "file.txt", "text": "VGVzdA=="}]',
                'autofill_enable': True,
                'l10n_mx_edi_invoice_type': 'in'}
            }
        self.assertEqual(res_1, expected_res_1)

        documents_workflow.create_model = 'product.template'
        res_2 = documents_workflow.create_record(self.document)
        created_product = self.env['product.template'].search(
            [('name', '=', 'product created from Documents')], limit=1)
        expected_res_2 = {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'name': 'New product template',
            'context': {},
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': created_product.id,
            'view_id': False}
        self.assertEqual(res_2, expected_res_2)
