# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from json import dumps

import requests
from odoo import _, fields, models
from odoo.exceptions import UserError
from requests.exceptions import HTTPError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    xunnel_token = fields.Char()

    def _xunnel(self, endpoint, payload=None):
        """_xunnel calls xunnel.com and returns it response.
            if is there any an exception. The error message within the API
            response will be raised.
        """
        self.ensure_one()
        if not self.xunnel_token:
            raise UserError(_('You need to define Xunnel Token'))
        base = self.env['ir.config_parameter'].sudo().get_param('account_xunnel.xunnel_server_url')
        origin_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        response = requests.post(
            str(base) + endpoint,
            headers={
                'Xunnel-Token': str(self.xunnel_token),
                'Xunnel-Origin': origin_url
            },
            data=dumps(payload) if payload else None)
        try:
            response.raise_for_status()
        except HTTPError as error:
            raise UserError(error)
        return response.json()

    def _sync_xunnel_providers(self, providers=None):
        """Requests https://wwww.xunnel.com/ to retrive all providers
        related to the current company and check them in the database
        to create them if they're not. After sync journals.
        """
        self.ensure_one()
        params = {}
        if providers:
            params['provider_account_identifier'] = providers
        links_response = self._xunnel('get_xunnel_providers', params)

        error = links_response.get('error')
        if error:
            return False, error
        all_links = links_response.get('response')
        for link in all_links:
            online_link = self.env['account.online.link'].search([
                ('is_xunnel', '=', True),
                ('client_id', '!=', False),
                ('client_id', '=', link.get('provider_account_identifier')),
                ('company_id', '=', self.id)], limit=1)
            new_info = {
                'client_id': link.get('provider_account_identifier'),
                'company_id': self.id,
                'auto_sync': False,
                'last_refresh': fields.Datetime.now(),
                'is_xunnel': True,
                'state': 'connected',
                'name': link.get('name'),
                'provider_data': 'xunnel',
            }
            if online_link:
                online_link.write(new_info)
            else:
                online_link = online_link.create(new_info)
            online_link.sync_journals()
        return True, all_links
