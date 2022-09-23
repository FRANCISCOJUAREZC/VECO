# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_mx_edi_get_payment_cfdi_values(self, move):
        result = super(
            AccountEdiFormat, self)._l10n_mx_edi_get_payment_cfdi_values(move)
        for invoice_vals in result.get('invoice_vals_list', []):
            payments = invoice_vals['invoice']._get_reconciled_payments()
            payments_count = len(payments)
            reconciled_lines = invoice_vals['invoice'].line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            reconciled_amls = reconciled_lines.mapped('matched_debit_ids.debit_move_id') + \
                reconciled_lines.mapped('matched_credit_ids.credit_move_id')
            for reconciled_aml in reconciled_amls:
                if reconciled_aml.payment_id and reconciled_aml.payment_id in payments:
                    continue
                payments_count += 1
            invoice_vals['number_of_payments'] = payments_count
        return result
