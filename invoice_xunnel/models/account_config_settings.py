# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.addons.account_xunnel.models.account_config_settings import \
    assert_xunnel_token


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xunnel_last_sync = fields.Date(
        string='Last Sync with Xunnel',
        related='company_id.xunnel_last_sync',
        readonly=False)

    @api.multi
    @assert_xunnel_token
    def sync_xunnel_attachments(self):
        return self.company_id.get_xml_sync_action()
