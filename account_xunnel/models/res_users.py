from odoo import _, api, models
from odoo.exceptions import UserError


class ResUsers(models.Model):

    _inherit = 'res.users'

    @api.model
    def get_xunnel_token(self):
        msg = _('You cannot add new accounts if your company does not have a valid token')
        if not self.env.company.xunnel_token:
            raise UserError(msg)
        res = self.env.company._xunnel('account_manager/info')
        info = res.get('response', {})
        if not info.get('token'):
            raise UserError(res.get('error'))
        info['locale'] = self.env.context.get('lang', 'en_US').split('_')[0]
        return info
