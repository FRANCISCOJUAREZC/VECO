
from odoo import models, api, fields


class AttachmentslsWizard(models.TransientModel):
    _name = 'xunnel.attachments.wizard'
    _description = 'Xunnel attachments sync'

    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.user.company_id)
    date_from = fields.Date(
        related='company_id.xunnel_last_sync',
        readonly=False)

    @api.multi
    def synchronize_attachments(self):
        return self.company_id.get_xml_sync_action()
