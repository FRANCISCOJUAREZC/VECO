# -*- coding: utf-8 -*-
# Copyright 2026 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
"""Second round of Odoo 19 fixes found while testing Pruebas2025.

1. ``web.asset_styles_company_report`` (the ``ir.attachment`` holding the
   per-company report SCSS) was lost during the migration. Without it the
   ``web.report_assets_common`` CSS bundle fails to compile ("Could not get
   content for web/static/asset_styles_company_report.scss"), so *every* PDF
   is printed without Bootstrap/layout styles: no header/footer, no table
   formatting. Recreate it and regenerate its content.

2. Studio-duplicated QWeb reports (``*_copy_N`` keys and their anonymous
   ``gen_key.*``/Studio overlays) still reference fields/helpers removed in
   Odoo 17-19. 2.0.3 only fixed a hard-coded list of MRP views; users kept
   duplicating reports afterwards, so apply the fixes generically to every
   non-module QWeb view, on every stored translation of ``arch_db``.

3. The Studio ``document_tax_totals`` copies still built for the Odoo 16
   ``tax_totals`` dict (``formatted_amount``, ``groups_by_subtotal``) are
   rewritten to the Odoo 19 structure, keeping the "Descuento" row.

4. ``purchase_request`` form/list views (and the VECO and Studio overlays on
   top of them) were left inactive, so the PR form fell back to an
   auto-generated view with no "Create RFQ" button. Reactivate them, after
   fixing the Studio overlay's references to fields removed in Odoo 19
   (``analytic_account_id``, ``analytic_tag_ids``, ``product_uom_category_id``,
   ``group_id``).

5. A few journal items on reconcilable accounts have a NULL
   ``amount_residual``, which crashes bank statement auto-reconciliation
   (``TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'``).
   Recompute it.

6. Menus still pointing to Odoo <= 15 ``account.financial.html.report``
   client actions (e.g. "Balance Sheet") are repointed to their Odoo 19
   ``account.report`` action.
"""

import json
import logging
import re

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. Company report styles
# --------------------------------------------------------------------------

STYLE_ATTACHMENT_URL = "web/static/asset_styles_company_report.scss"


def _restore_company_report_styles(env):
    attachment = env.ref("web.asset_styles_company_report", raise_if_not_found=False)
    if not attachment:
        Attachment = env["ir.attachment"].sudo()
        attachment = Attachment.search([("url", "=", STYLE_ATTACHMENT_URL)], limit=1)
        if not attachment:
            attachment = Attachment.create({
                "name": "res.company.scss",
                "mimetype": "text/scss",
                "type": "binary",
                "url": STYLE_ATTACHMENT_URL,
                "datas": env["res.company"]._get_asset_style_b64(),
            })
            _logger.info("Recreated web.asset_styles_company_report attachment")
        env["ir.model.data"].create({
            "module": "web",
            "name": "asset_styles_company_report",
            "model": "ir.attachment",
            "res_id": attachment.id,
            "noupdate": False,
        })
    env["res.company"]._update_asset_style()


# --------------------------------------------------------------------------
# 2. Generic QWeb fixes on Studio/custom report views
# --------------------------------------------------------------------------

# (regex, replacement) applied to every non-module QWeb view.
QWEB_GENERIC_FIXES = [
    # mrp.production
    (r"\bo\.date_planned_start\b", "o.date_start"),
    (r"\bo\.date_planned_finished\b", "o.date_finished"),
    # stock.move: reserved_availability/quantity_done merged into `quantity`
    (r"\.reserved_availability\b", ".quantity"),
    (r"\.quantity_done\b", ".quantity"),
    # stock.picking
    (r"\bmove_ids_without_package\b", "move_ids"),
    (r"\bo\.move_lines\b", "o.move_ids"),
    (r"\bo\.weight_uom_id\b", "o.weight_uom_name"),
    # stock.package_level was removed: skip the "entire packs" table
    (r"t-if=\"o\.package_level_ids and o\.picking_type_entire_packs\"", 't-if="False"'),
    # mrp.routing was removed (Odoo 14); the Studio field lives on mrp.bom now
    (r"\bo\.routing_id\.x_studio_etiquetas_1\b", "o.bom_id.x_studio_etiquetas_1"),
    (r"<span t-field=\"o\.routing_id\.note\"/>", ""),
    # Studio fields deleted before the migration
    (r"<span t-field=\"o\.x_studio_field_f55Mz\.note\"/>", ""),
    (r"<span t-field=\"doc\.x_studio_field_k7pyQ\.x_condicion\"/>", ""),
    # account.move
    (r"\bo\.residual\b", "o.amount_residual"),
    (
        r"o\.partner_bank_id\.build_qr_code_url\(o\.amount_residual,\s*\(o\.reference\) if \(o\.reference\) else o\.number\)",
        "o.partner_bank_id.build_qr_code_url(o.amount_residual, o.payment_reference or o.name, "
        "None, o.currency_id, o.partner_id)",
    ),
    # `to_text` is no longer exposed to QWeb; `image_data_uri` is.
    (
        r"'data:image/png;base64,%s' % to_text\(([\w\.]+)\)",
        r"image_data_uri(\1)",
    ),
]

# Only for views whose root template is a sale/purchase order report:
# sale.order.line / purchase.order.line `product_uom` -> `product_uom_id`.
# (stock.move still has `product_uom`, so this can't be applied globally.)
ORDER_REPORT_ROOT_PREFIXES = (
    "sale.report_saleorder",
    "purchase.report_purchaseorder",
    "purchase.report_purchasequotation",
)
QWEB_ORDER_LINE_FIXES = [
    (r"\bline\.product_uom(?!\w)", "line.product_uom_id"),
    (r"\bline\.taxes_id\b", "line.tax_ids"),
    (r"\bline\.tax_id\b", "line.tax_ids"),
    (r"\bo\.notes\b", "o.note"),
]

# Odoo 19 version of the Studio "document_tax_totals" copies, keeping VECO's
# "Descuento" row. Based on account.document_tax_totals_copy_9, which was
# already fixed by hand in Pruebas2025.
TAX_TOTALS_TEMPLATE = """<t t-name="{name}">
            <t t-set="currency" t-value="currency or (o and o.currency_id) or (doc and doc.currency_id)"/>
            <t t-set="same_tax_base" t-value="tax_totals['same_tax_base']"/>
            <t t-foreach="tax_totals['subtotals']" t-as="subtotal">
                <tr class="border-black o_subtotal">
                    <td><strong t-esc="subtotal['name']"/></td>
                    <td class="text-end">
                        <span t-att-class="oe_subtotal_footer_separator" t-out="subtotal['base_amount_currency']" t-options="{{'widget': 'monetary', 'display_currency': currency}}"/>
                    </td>
                </tr>
                <t t-set="total_discount" t-value="0"/>
                <t t-if="o">
                    <t t-set="lines" t-value="o.invoice_line_ids"/>
                </t>
                <t t-if="doc">
                    <t t-set="lines" t-value="doc.order_line"/>
                </t>
                <t t-foreach="lines" t-as="line">
                    <t t-if="o">
                        <t t-set="quantity" t-value="line.quantity"/>
                    </t>
                    <t t-if="doc">
                        <t t-set="quantity" t-value="line.product_uom_qty"/>
                    </t>
                    <t t-set="line_discount_price_unit" t-value="line.price_unit * (line.discount / 100.0)"/>
                    <t t-set="line_discount" t-value="quantity * line_discount_price_unit"/>
                    <t t-set="total_discount" t-value="total_discount + line_discount"/>
                </t>
                <tr t-if="total_discount" class="border-black o_subtotal">
                    <td><strong>Descuento</strong></td>
                    <td class="text-end">
                        <span t-att-class="oe_subtotal_footer_separator" t-esc="round(total_discount, 2)" t-options="{{'widget': 'monetary', 'display_currency': currency}}"/>
                    </td>
                </tr>
                <t t-foreach="subtotal['tax_groups']" t-as="tax_group">
                    <tr class="o_taxes">
                        <t t-if="same_tax_base or tax_group['display_base_amount_currency'] is False">
                            <td style="max-width: 200px;">
                                <span t-out="tax_group['group_name']"/>
                            </td>
                            <td class="text-end o_price_total">
                                <span class="text-nowrap" t-out="tax_group['tax_amount_currency']" t-options="{{'widget': 'monetary', 'display_currency': currency}}"/>
                            </td>
                        </t>
                        <t t-else="">
                            <td>
                                <span t-out="tax_group['group_name']"/>
                                <span> on </span>
                                <span class="text-nowrap" t-out="tax_group['display_base_amount_currency']" t-options="{{'widget': 'monetary', 'display_currency': currency}}"/>
                            </td>
                            <td class="text-end o_price_total">
                                <span class="text-nowrap" t-out="tax_group['tax_amount_currency']" t-options="{{'widget': 'monetary', 'display_currency': currency}}"/>
                            </td>
                        </t>
                    </tr>
                </t>
            </t>
            <tr class="border-black o_total">
                <td><strong>Total</strong></td>
                <td class="text-end">
                    <span t-out="tax_totals['total_amount_currency']" t-options="{{'widget': 'monetary', 'display_currency': currency}}"/>
                </td>
            </tr>
        </t>"""


def _apply_regex_fixes(arch, fixes):
    for pattern, repl in fixes:
        arch = re.sub(pattern, repl, arch)
    return arch


def _write_arch_db(cr, view_id, arch_db):
    cr.execute(
        "UPDATE ir_ui_view SET arch_db = %s WHERE id = %s",
        (json.dumps(arch_db), view_id),
    )


def _fix_custom_qweb_views(cr):
    # Non-module QWeb views: no xmlid, or a Studio/export one.
    cr.execute("""
        SELECT v.id, v.key, v.inherit_id, v.arch_db
          FROM ir_ui_view v
         WHERE v.type = 'qweb'
           AND NOT EXISTS (
                SELECT 1 FROM ir_model_data d
                 WHERE d.model = 'ir.ui.view' AND d.res_id = v.id
                   AND d.module NOT IN ('studio_customization', '__export__', '__custom__')
           )
    """)
    views = {row[0]: row for row in cr.fetchall()}
    cr.execute("SELECT id, key, inherit_id FROM ir_ui_view WHERE type = 'qweb'")
    all_views = {row[0]: row for row in cr.fetchall()}

    def root_key(view_id):
        seen = set()
        while view_id in all_views and view_id not in seen:
            seen.add(view_id)
            _vid, key, parent = all_views[view_id]
            if not parent:
                return key or ""
            view_id = parent
        return ""

    fixed = 0
    for view_id, (_vid, key, _parent, arch_db) in views.items():
        if not arch_db:
            continue
        is_order_report = root_key(view_id).startswith(ORDER_REPORT_ROOT_PREFIXES)
        is_old_tax_totals = (key or "").startswith("account.document_tax_totals_copy")
        changed = False
        for lang, arch in arch_db.items():
            if not arch:
                continue
            if is_old_tax_totals and "formatted_amount" in arch:
                new_arch = TAX_TOTALS_TEMPLATE.format(name=key)
            else:
                new_arch = _apply_regex_fixes(arch, QWEB_GENERIC_FIXES)
                if is_order_report:
                    new_arch = _apply_regex_fixes(new_arch, QWEB_ORDER_LINE_FIXES)
            if new_arch != arch:
                arch_db[lang] = new_arch
                changed = True
        if changed:
            _write_arch_db(cr, view_id, arch_db)
            fixed += 1
    _logger.info("Fixed %s custom QWeb views for Odoo 19", fixed)


# --------------------------------------------------------------------------
# 4. Purchase request views
# --------------------------------------------------------------------------

PURCHASE_REQUEST_VIEW_XMLIDS = [
    ("purchase_request", "view_purchase_request_form"),
    ("purchase_request", "purchase_request_line_tree"),
    ("purchase_request", "purchase_request_line_form"),
    ("purchase_request", "view_purchase_request_line_details"),
    ("purchase_request", "purchase_order_line_form2_sub"),
    ("purchase_request", "purchase_order_line_tree_sub"),
    ("veco_customizations", "view_purchase_request_veco_customizations_form"),
]

PR_STUDIO_OVERLAY = (
    "studio_customization",
    "odoo_studio_purchase_1e0a2d42-8b68-4b0c-a84d-6002acbdff2a",
)

PR_STUDIO_OVERLAY_FIXES = [
    # analytic_tag_ids no longer exists on purchase.request.line
    (
        r"<xpath expr=\"[^\"]*field\[@name='analytic_tag_ids'\]\" position=\"attributes\">.*?</xpath>\s*",
        "",
    ),
    (
        r"<field name=\"analytic_account_id\"[^>]*/>\s*<field name=\"analytic_tag_ids\"[^>]*/>",
        '<field name="analytic_distribution" widget="analytic_distribution" '
        'groups="analytic.group_analytic_accounting" readonly="is_editable == False"/>',
    ),
    (r"<field name=\"product_uom_category_id\"[^>]*/>\s*", ""),
    # purchase.request.group_id was removed: drop its attributes and anchor
    # the Studio fields that followed it on `description` instead.
    (
        r"<xpath expr=\"//field\[@name='group_id'\]\" position=\"attributes\">.*?</xpath>\s*",
        "",
    ),
    (
        r"<xpath expr=\"//field\[@name='group_id'\]\" position=\"after\">",
        "<xpath expr=\"//field[@name='description']\" position=\"after\">",
    ),
]


def _xmlid_res_id(cr, module, name):
    cr.execute(
        "SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s AND model = 'ir.ui.view'",
        (module, name),
    )
    row = cr.fetchone()
    return row and row[0]


def _activate_view_checked(cr, env, view_id, label):
    """Activate a view, rolling back if it no longer validates."""
    try:
        with cr.savepoint():
            cr.execute("UPDATE ir_ui_view SET active = true WHERE id = %s", (view_id,))
            env.invalidate_all()
            env["ir.ui.view"].browse(view_id)._check_xml()
    except Exception:
        _logger.warning("Could not reactivate view %s (%s)", label, view_id, exc_info=True)
        env.invalidate_all()


def _fix_purchase_request_views(cr, env):
    for module, name in PURCHASE_REQUEST_VIEW_XMLIDS:
        view_id = _xmlid_res_id(cr, module, name)
        if view_id:
            _activate_view_checked(cr, env, view_id, f"{module}.{name}")

    view_id = _xmlid_res_id(cr, *PR_STUDIO_OVERLAY)
    if not view_id:
        return
    cr.execute("SELECT arch_db FROM ir_ui_view WHERE id = %s", (view_id,))
    arch_db = cr.fetchone()[0] or {}
    for lang, arch in arch_db.items():
        if not arch:
            continue
        for pattern, repl in PR_STUDIO_OVERLAY_FIXES:
            arch = re.sub(pattern, repl, arch, flags=re.DOTALL)
        arch_db[lang] = arch
    _write_arch_db(cr, view_id, arch_db)
    _activate_view_checked(cr, env, view_id, ".".join(PR_STUDIO_OVERLAY))


# --------------------------------------------------------------------------
# 5. NULL amount_residual
# --------------------------------------------------------------------------

def _recompute_null_amount_residual(cr, env):
    cr.execute("""
        SELECT aml.id
          FROM account_move_line aml
          JOIN account_account acc ON acc.id = aml.account_id
         WHERE aml.amount_residual IS NULL
           AND (acc.reconcile OR acc.account_type IN ('asset_cash', 'liability_credit_card'))
    """)
    ids = [row[0] for row in cr.fetchall()]
    if not ids:
        return
    lines = env["account.move.line"].browse(ids)
    env.add_to_compute(lines._fields["amount_residual"], lines)
    env.add_to_compute(lines._fields["amount_residual_currency"], lines)
    env.add_to_compute(lines._fields["reconciled"], lines)
    lines.flush_recordset()
    _logger.info("Recomputed amount_residual on %s journal items", len(ids))


# --------------------------------------------------------------------------
# 6. Legacy financial report actions
# --------------------------------------------------------------------------

# Odoo <= 15 `account.financial.html.report` client actions whose report no
# longer exists (opening them raises "Expected singleton: account.report()").
# Repoint their menus to the Odoo 19 equivalent when there is one.
LEGACY_REPORT_ACTION_REPLACEMENTS = {
    "account_reports.account_financial_html_report_action_2": "account_reports.action_account_report_bs",
}


def _repoint_legacy_report_menus(env):
    for old_xmlid, new_xmlid in LEGACY_REPORT_ACTION_REPLACEMENTS.items():
        old_action = env.ref(old_xmlid, raise_if_not_found=False)
        new_action = env.ref(new_xmlid, raise_if_not_found=False)
        if not old_action or not new_action:
            continue
        menus = env["ir.ui.menu"].with_context(active_test=False).search([
            ("action", "=", f"{old_action._name},{old_action.id}"),
        ])
        menus.write({"action": f"{new_action._name},{new_action.id}"})


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _restore_company_report_styles(env)
    _repoint_legacy_report_menus(env)
    _fix_custom_qweb_views(cr)
    env.invalidate_all()
    _fix_purchase_request_views(cr, env)
    _recompute_null_amount_residual(cr, env)
