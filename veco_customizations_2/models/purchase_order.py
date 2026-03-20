# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        result = super(PurchaseOrder, self)._prepare_invoice()
        move_type = self._context.get('default_move_type', 'in_invoice')
        # v18+: _get_default_journal() fue reemplazado por _search_default_journal()
        journal = self.env['account.move'].with_context(
            default_move_type=move_type)._search_default_journal()
        result['journal_id'] = journal.id
        return result
