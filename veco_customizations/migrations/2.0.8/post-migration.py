# -*- coding: utf-8 -*-
# Copyright 2026 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
"""Customer review of the sale and invoice reports (SO30268 / V15327).

Sale reports (report/sale_order_templates.xml): the "Impuestos" column is
replaced by "Descuento (%)" and the untaxed subtotal reads "Importe sin
impuestos".

"Factura Nacional Veco" (standard report, l10n_mx_edi document) gets the
VECO additions through report/account_move_templates.xml.

"Factura Dolares VECO": its Studio document
``account.report_invoice_document_with_payments_copy_3_copy_2_copy_2`` (and
its Studio overlay) only showed the CFDI data, product code, usage and
payment way when ``l10n_mx_edi_cfdi_uuid`` was set, which is empty on the
invoices migrated from Odoo 15; it also duplicated the customer address and
printed an empty extra column when there was a discount. The document is
rewritten to a thin ``t-call`` of
``veco_customizations.report_invoice_veco_usd_document``, which reads the
CFDI values from the XML attachment.
"""

import json
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

USD_DOCUMENT = "account.report_invoice_document_with_payments_copy_3_copy_2_copy_2"
USD_TEMPLATE = "veco_customizations.report_invoice_veco_usd_document"


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    View = env["ir.ui.view"].with_context(active_test=False)
    view = View.search([("key", "=", USD_DOCUMENT), ("type", "=", "qweb")], limit=1)
    if not view:
        _logger.info("Report %s not found, skipped", USD_DOCUMENT)
        return
    overlays = View.search([("inherit_id", "=", view.id)])
    if overlays:
        _logger.info("Report %s: removing Studio overlays %s", USD_DOCUMENT, overlays.mapped("key"))
        overlays.unlink()
    arch = '<t t-name="%s">\n    <t t-call="%s"/>\n</t>' % (USD_DOCUMENT, USD_TEMPLATE)
    cr.execute("SELECT arch_db FROM ir_ui_view WHERE id = %s", (view.id,))
    langs = set(cr.fetchone()[0] or {}) | {"en_US"}
    cr.execute(
        "UPDATE ir_ui_view SET arch_db = %s, active = TRUE WHERE id = %s",
        (json.dumps({lang: arch for lang in langs}), view.id),
    )
    env.registry.clear_cache("templates")
    _logger.info("Report %s rewritten to %s", USD_DOCUMENT, USD_TEMPLATE)
