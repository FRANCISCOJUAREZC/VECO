# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _l10n_mx_edi_get_payment_policy(self):
        """Method Overriden in order to set PUE always if the
        payment term days is greather than zero, PPD otherwise"""
        self.ensure_one()
        res = super(AccountInvoice, self)._l10n_mx_edi_get_payment_policy()
        version = self.l10n_mx_edi_get_pac_version()
        if version == '3.2':
            return res
        version = self.l10n_mx_edi_get_pac_version()
        term_ids = self.payment_term_id.line_ids
        term_pue = self.env.ref('account.account_payment_term_immediate')
        if self.payment_term_id == term_pue:
            res = 'PUE'
        elif len(term_ids) == 1:
            if not term_ids.days:
                res = 'PUE'
            else:
                res = 'PPD'
        elif len(term_ids > 1):
            res = 'PPD'
        else:
            res = ''
        return res
