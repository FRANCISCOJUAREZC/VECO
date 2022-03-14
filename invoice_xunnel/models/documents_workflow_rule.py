# -*- coding: utf-8 -*-
from json import dumps

from odoo import fields, models


class WorkflowActionRuleAccountInherit(models.Model):
    _inherit = 'documents.workflow.rule'

    create_model = fields.Selection(selection_add=[('xunnel.invoice', 'Xunnel Invoice')])

    def create_record(self, documents=None):
        response = super().create_record(documents=documents)
        if self.create_model != 'xunnel.invoice':
            return response
        files = []
        for xml in documents:
            content = xml.datas.decode() if xml.datas else ''
            files.append({'name': xml.name, 'text': content})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'attach.xmls.wizard',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'file_names': dumps(files),
                'autofill_enable': True,
                'l10n_mx_edi_invoice_type': 'in',
            }
        }
