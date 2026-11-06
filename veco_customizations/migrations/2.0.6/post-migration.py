# -*- coding: utf-8 -*-
# Copyright 2026 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
"""Clean layout for the VECO / DVI purchase, sale and manufacturing reports.

The Studio report copies (``purchase.report_purchaseorder_document_copy_*``)
were designed for Odoo 13-16. In Odoo 19 ``web.external_layout`` renders
their ``address``/``information_block`` variables on top of the custom body
(duplicating supplier and shipping addresses), the draft "Request for
Quotation #" heading shows next to the custom title, and the pixel offsets
Studio added (``margin-left: 50px``, ``-95px``...) misalign everything.

Each document view is rewritten to a thin ``t-call`` of
``veco_customizations.report_purchaseorder_veco_document`` that keeps its
own texts (bill-to, contact, revision code, language, extra sections), and
its Studio overlays (already folded into those texts) are removed.
Obsolete copies ("OBSOLETO") are left untouched.

The same applies to the Studio quotation / sale order copies
(``sale.report_saleorder_document_copy_*``, same address duplication) and to
the manufacturing order copies (``mrp.report_mrporder_copy_*``: the
"Lista de materiales" label printed one letter per line because of a
``margin-right: 1200px``, misaligned component table, empty barcode).

Finally, Odoo 19 renamed the ``type`` parameter of ``/report/barcode/`` to
``barcode_type``; the old URL returns a 500 error and the barcode prints as
an empty box. It is fixed in every custom QWeb view (invoices, pickings...).
"""

import json
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

TEMPLATE = "veco_customizations.report_purchaseorder_veco_document"
SALE_TEMPLATE = "veco_customizations.report_saleorder_veco_document"
MRP_TEMPLATE = "veco_customizations.report_mrporder_veco_document"

BILL_TO_VECO = "Veco, S.A. de C.V.<br/>Calle 13 Este No. 116, CIVAC<br/>Jiutepec, Mor. C.P. 62578"
BILL_TO_DVI = (
    "De Vecchi Ingenieros, S.A. de C.V.<br/>Pirineos No. 263, Col. Santa Cruz Atoyac<br/>"
    "Alcaldía Benito Juárez, CDMX, México, C.P. 03310"
)
DOCS_ADDRESS_VECO = (
    "Calle 13 Este No. 116, CIVAC<br/>Jiutepec, Mor. 62578, México<br/>"
    "At'n. Depto. de Procuramiento y Suministros"
)
CONTACT_VENTAS = "Tel. 56-88-35-66; 56-88-39-77<br/>ventas@veco.mx"
CONTACT_GDEMENDOZA = "Tel. 777 329 2650 Ext. 504<br/>g.demendoza@veco.mx"
OFFICE = "<strong>Oficinas / almacén tráfico</strong><br/>Pirineos 263, Col. Sta. Cruz Atoyac<br/>México, D.F. C.P. 03340<br/>Tel. 56-88-35-66; 56-88-39-77<br/>%s"
SIGN_ES = ["Autorizó", "Solicitó", "Compras"]
SIGN_EN = ["Required by", "Authorization", "Signature"]

# document view key -> parameters for TEMPLATE
REPORTS = {
    # Orden de Compra Veco Nacional FV-07-8-001 REV.7; 07/26
    "purchase.report_purchaseorder_document_copy_1_copy_3_copy_2": {
        "bill_to": BILL_TO_VECO,
        "veco_contact": CONTACT_VENTAS,
        "revision": "REV.7; 07/26 FV-07-8-001",
        "show_line_date": True,
        "signatures": SIGN_ES,
    },
    # Orden de Compra En desarrollo No USAR
    "purchase.report_purchaseorder_document_copy_1_copy_3_copy_1": {
        "bill_to": BILL_TO_VECO,
        "veco_contact": CONTACT_GDEMENDOZA,
        "revision": "REV.6; 07/24 FV-07-8-001",
        "show_line_date": True,
        "show_specs": True,
    },
    # Orden de Compra Veco Anterior
    "purchase.report_purchaseorder_document_copy_1": {
        "bill_to": BILL_TO_VECO,
        "office": OFFICE % "vecosa@prodigy.net.mx",
        "veco_contact": CONTACT_VENTAS,
        "revision": "Rev.3; 01/20 FV-07-8-001",
        "show_delivery_date": True,
        "signatures": SIGN_ES,
    },
    # Orden de Compra Dvi
    "purchase.report_purchaseorder_document_copy_1_copy_1": {
        "bill_to": BILL_TO_DVI,
        "office": OFFICE % "compras@dvi.mx",
        "revision": "Rev.1; 06/21 FDV-C-003",
        "use_create_date": True,
        "show_delivery_date": True,
        "show_request_info": True,
    },
    # Orden de Compra Veco Internacional Rev. 5 04/25 FV-07-8-003
    "purchase.report_purchaseorder_document_copy_1_copy_2_copy_5": {
        "en": True,
        "international": True,
        "bill_to": BILL_TO_VECO,
        "docs_address": DOCS_ADDRESS_VECO,
        "revision": "Rev. 5; 04/25 FV-07-8-003",
        "show_delivery_date": True,
        "signatures": SIGN_EN,
    },
    # Orden de Compra DVI Internacional
    "purchase.report_purchaseorder_document_copy_1_copy_2_copy_4": {
        "en": True,
        "international": True,
        "bill_to": BILL_TO_DVI,
        "docs_address": BILL_TO_DVI,
        "revision": "REV.3; 04/21 FV-07-8-003",
        "show_delivery_date": True,
        "signatures": SIGN_EN,
    },
}

QUOTE = {"quote": True}
ORDER = {"quote": False}

# sale document view key -> parameters for SALE_TEMPLATE
SALE_REPORTS = {
    # Cotización DVI
    "sale.report_saleorder_document_copy_1_copy_2": dict(
        QUOTE, title="Cotización Filtros", show_services=True,
        revision="REV. 1;01/20 FV-06-8-001"),
    # Cotización Equipos REV. 4, 03/25
    "sale.report_saleorder_document_copy_1_copy_2_copy_1": dict(
        QUOTE, title="Cotización Equipos", show_shipping_method=True,
        revision="REV. 0;08/19 FDV-I-001"),
    # Cotización Filtros REV. 4, 03/25
    "sale.report_saleorder_document_copy_1_copy_2_copy_2": dict(
        QUOTE, title="Cotización Filtros", show_shipping_method=True,
        revision="REV. 0;08/19 FDV-I-001"),
    # Cotización VECO (Servicios) Rev. 4; 03/25
    "sale.report_saleorder_document_copy_1_copy_2_copy_3_copy_2": dict(
        QUOTE, title="Cotización", show_services=True,
        revision="REV. 3;03/23 FV-06-8-001"),
    # Pedido CID DVI
    "sale.report_saleorder_document_copy_1_copy_1": dict(ORDER, title="Pedido"),
    # Pedido N DVI
    "sale.report_saleorder_document_copy_1_copy_1_copy_2": dict(
        ORDER, title="Pedido", revision="Rev. 0;08/19"),
    # Pedido Veco REV. 8; 03/25
    "sale.report_saleorder_document_copy_1_copy_1_copy_2_copy_1": dict(
        ORDER, title="Pedido", revision="Rev. 0;08/19"),
    # Pedido Veco PL1 Rev. 08,02/26 FV-02-8-001
    "sale.report_saleorder_document_copy_1_copy_1_copy_2_copy_1_copy_1_copy_1": dict(
        ORDER, title="Pedido", work_order=True, show_shipping_method=True,
        banner="ORDEN DE TRABAJO PARA VECO, S.A. DE C.V.<br/>DIVISIÓN DE EQUIPOS",
        revision="Rev. 07;02/24 FV-02-8-001"),
}

TITLE_LISTA = "LISTA DE EXPEDICIÓN"
TITLE_PL1 = "LISTA DE EXPEDICIÓN<br/>ÓRDENES DE PRODUCCIÓN PL1"
TITLE_PL2 = "LISTA DE EXPEDICIÓN<br/>ÓRDENES DE PRODUCCIÓN"

# manufacturing report view key (the full report, not a document view)
# -> parameters for MRP_TEMPLATE
MRP_REPORTS = {
    # Lista de Expedición
    "mrp.report_mrporder_copy_1_copy_3": dict(
        title=TITLE_LISTA, revision="Rev. 7;02/20 FV-02-8-009"),
    # Lista de Expedición P2 Rev. 11;08/26 FV-02-8-009
    "mrp.report_mrporder_copy_1_copy_4_copy_1": dict(
        title=TITLE_LISTA, revision="Rev. 11;08/26 FV-02-8-009"),
    # Orden de producción PL1
    "mrp.report_mrporder_copy_1_copy_1": dict(
        title=TITLE_PL1, show_details=True, revision="Rev. 7;02/20 FV-02-8-009"),
    # Orden de producción PL1 Rev. 11; 08/26 FV-02-8-009
    "mrp.report_mrporder_copy_1_copy_1_copy_1_copy_1": dict(
        title=TITLE_PL1, show_details=True, revision="Rev. 11; 08/26 FV-02-8-009"),
    # Orden de producción PL2
    "mrp.report_mrporder_copy_1_copy_2_copy_1": dict(
        title=TITLE_PL2, show_details=True, show_workorders=True,
        revision="Rev. 5;03/20 FV-04-8-008"),
    # Orden de producción PL2 REV. 8;09/25 FV-04-8-008
    "mrp.report_mrporder_copy_1_copy_2_copy_2": dict(
        title=TITLE_PL2, show_details=True, show_workorders=True,
        show_labels=True, show_data_log=True, revision="REV. 8;09/25 FV-04-8-008"),
}

MARKUP_PARAMS = (
    "bill_to", "office", "veco_contact", "docs_address", "revision", "title", "banner",
)

# Odoo <= 16 barcode URL -> Odoo 19 (the "type" parameter became "barcode_type")
BARCODE_OLD = "/report/barcode/?type="
BARCODE_NEW = "/report/barcode/?barcode_type="


def _set_lines(params, indent):
    lines = []
    for name, value in params.items():
        if name in MARKUP_PARAMS:
            lines.append('%s<t t-set="%s">%s</t>' % (indent, name, value))
        else:
            lines.append('%s<t t-set="%s" t-value="%r"/>' % (indent, name, value))
    return lines


def build_arch(key, params, template=TEMPLATE):
    """Return the QWeb arch of a document copy calling the shared template."""
    lines = ['<t t-name="%s">' % key, '    <t t-call="%s">' % template]
    lines += _set_lines(params, " " * 8)
    lines += ["    </t>", "</t>"]
    return "\n".join(lines)


def build_mrp_arch(key, params, template=MRP_TEMPLATE):
    """Return the arch of a full manufacturing report calling the shared template."""
    lines = [
        '<t t-name="%s">' % key,
        '    <t t-call="web.html_container">',
        '        <t t-foreach="docs" t-as="o">',
        '            <t t-call="%s">' % template,
    ]
    lines += _set_lines(params, " " * 16)
    lines += ["            </t>", "        </t>", "    </t>", "</t>"]
    return "\n".join(lines)


def all_reports():
    """(view key, arch) of every report rewritten by this migration."""
    for key, params in REPORTS.items():
        yield key, build_arch(key, params, TEMPLATE)
    for key, params in SALE_REPORTS.items():
        yield key, build_arch(key, params, SALE_TEMPLATE)
    for key, params in MRP_REPORTS.items():
        yield key, build_mrp_arch(key, params)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    View = env["ir.ui.view"].with_context(active_test=False)
    for key, arch in all_reports():
        view = View.search([("key", "=", key), ("type", "=", "qweb")], limit=1)
        if not view:
            _logger.info("Report %s not found, skipped", key)
            continue
        overlays = View.search([("inherit_id", "=", view.id)])
        if overlays:
            _logger.info("Report %s: removing Studio overlays %s", key, overlays.mapped("key"))
            overlays.unlink()
        langs = _arch_langs(cr, view.id)
        cr.execute(
            "UPDATE ir_ui_view SET arch_db = %s, active = TRUE WHERE id = %s",
            (json.dumps({lang: arch for lang in langs}), view.id),
        )
        _logger.info("Report %s rewritten to a shared VECO template", key)
    _fix_barcode_urls(cr)
    env.registry.clear_cache("templates")


def _fix_barcode_urls(cr):
    """Rename the barcode URL parameter in every stored translation of arch_db."""
    cr.execute(
        """
        UPDATE ir_ui_view v
           SET arch_db = (
                SELECT jsonb_object_agg(t.key, replace(t.value, %s, %s))
                  FROM jsonb_each_text(v.arch_db) t)
         WHERE v.type = 'qweb'
           AND v.arch_db::text LIKE %s
        RETURNING v.key
        """,
        (BARCODE_OLD, BARCODE_NEW, "%" + BARCODE_OLD + "%"),
    )
    keys = [row[0] for row in cr.fetchall()]
    _logger.info("Barcode URL fixed in %s QWeb views: %s", len(keys), keys)


def _arch_langs(cr, view_id):
    cr.execute("SELECT arch_db FROM ir_ui_view WHERE id = %s", (view_id,))
    current = cr.fetchone()[0] or {}
    return set(current) | {"en_US"}
