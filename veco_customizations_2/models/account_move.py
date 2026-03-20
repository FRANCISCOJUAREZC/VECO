# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _l10n_mx_edi_cfdi_invoice_get_reconciled_payments_values(self):
        """Override para incluir en number_of_payments los asientos directos
        de diarios banco/efectivo que estén reconciliados con la factura pero
        que no fueron registrados como account.payment ni como statement line.

        En v15 esto se hacía en account.edi.format._l10n_mx_edi_get_payment_cfdi_values.
        En v17+ account.edi.format fue eliminado; la lógica equivalente vive aquí.
        """
        results = super()._l10n_mx_edi_cfdi_invoice_get_reconciled_payments_values()

        invoices = self.filtered(
            lambda x: x.is_invoice() and x.l10n_mx_edi_cfdi_state == 'sent')

        for invoice in invoices:
            if invoice not in results or not results[invoice]:
                continue

            # Líneas de la factura en cuentas por cobrar/pagar
            pay_rec_lines = invoice.line_ids.filtered(
                lambda line: line.account_type in ('asset_receivable', 'liability_payable'))

            # Contrapartidas reconciliadas (move lines)
            reconciled_amls = (
                pay_rec_lines.mapped('matched_debit_ids.debit_move_id') +
                pay_rec_lines.mapped('matched_credit_ids.credit_move_id')
            )

            # Movimientos que ya están contados como pagos CFDI
            already_counted = {r['payment'] for r in results[invoice]}

            # Contar asientos banco/efectivo que no son CFDI payments (sin
            # origin_payment_id ni statement_line_id) pero sí están reconciliados
            extra_count = 0
            seen_moves = set()
            for aml_line in reconciled_amls:
                move = aml_line.move_id
                if move.id in seen_moves or move in already_counted:
                    continue
                seen_moves.add(move.id)
                if move.journal_id.type in ('bank', 'cash'):
                    extra_count += 1

            if extra_count:
                for pay_result in results[invoice]:
                    pay_result['number_of_payments'] += extra_count

        return results
