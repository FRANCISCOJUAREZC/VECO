# -*- coding: utf-8 -*-
# Copyright 2026 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
"""Repair and reactivate the Studio view overlays disabled by the Odoo 19
upgrade.

During the upgrade, every ``studio_customization.*`` overlay that no longer
validated (an xpath that cannot be located, a field renamed/removed since
Odoo 15) was deactivated *as a whole*, hiding all the custom ``x_studio_*``
fields it added (e.g. Importación / Entregado / Facturado / Solicitado Por on
the purchase order form).

2.0.3 tried to restore them by overwriting ``arch_db`` with the archs
hand-fixed in the Pruebas2025 database (``studio_views_fixup.json``), but on a
fresh database some of those xpaths still could not be located and ``-u``
crashed, so that call was commented out. This step is defensive instead:

1. Start from the hand-fixed arch when there is one
   (``studio_overlays_base.json``, the Studio entries of that same fixture),
   else from the view's own arch, and apply the known Odoo 19 renames.
2. Replay every top-level spec with Odoo's own inheritance engine on top of
   the current combined parent arch. A positional xpath that no longer
   matches is re-anchored on its named steps (``//field[@name='x']``); a spec
   that still cannot be applied is dropped and logged.
3. Write the result, activate the view and run ``_check_xml`` inside a
   savepoint. A ``Field "x" does not exist`` error strips that field and
   retries; any other error rolls the view back (it stays inactive, as
   before) and is logged. Nothing here can make the upgrade fail.

Every stored translation of ``arch_db`` is processed independently.
"""

import copy
import json
import logging
import os
import re

from lxml import etree

from odoo import SUPERUSER_ID, api
from odoo.tools.template_inheritance import apply_inheritance_specs, locate_node

_logger = logging.getLogger(__name__)

BASE_ARCHS_FILE = "studio_overlays_base.json"
MAX_VALIDATION_ROUNDS = 10

# (model or None for all, regex, replacement) applied to the raw arch.
RENAMES = [
    (None, r"\bmove_ids_without_package\b", "move_ids"),
    (None, r"\bmove_line_ids_without_package\b", "move_line_ids"),
    (None, r"\b__last_update\b", "write_date"),
    ("account.move", r"@name='amount_untaxed_signed'", "@name='amount_untaxed_in_currency_signed'"),
    # move_type is now an invisible sheet-level field: anchor the custom
    # header fields right after the customer/vendor block instead.
    (
        "account.move",
        r"//form\[1\]/sheet\[1\]/group\[1\]/group\[1\]/field\[@name='move_type'\]",
        "//group[@id='header_left_group']/div[1]",
    ),
    ("account.account", r"@name='type_id'", "@name='account_type'"),
    ("product.template", r"@name='uom_po_id'", "@name='uom_id'"),
    ("product.template", r"@name='priority'", "@name='is_favorite'"),
    ("project.task", r"@name='user_id'", "@name='user_ids'"),
    ("mrp.production", r"@name='production_duration_expected'", "@name='duration_expected'"),
    ("mrp.production", r"@name='production_real_duration'", "@name='duration'"),
]

LAST_NAMED_STEP = re.compile(r"(\w+)\[@name='([^']+)'\]$")
NAMED_STEP = re.compile(r"(\w+)\[@name='([^']+)'\]")
MISSING_FIELD = re.compile(
    r"""[Ff]ield ["“]([\w.]+)["”] does not exist in model ["“]([\w.]+)["”]"""
)
SUBVIEW_TAGS = {"list", "tree", "form", "kanban"}


def _apply_renames(model, arch):
    for rule_model, pattern, repl in RENAMES:
        if rule_model is None or rule_model == model:
            arch = re.sub(pattern, repl, arch)
    return arch


def _relaxed_expr(expr):
    """``/form[1]/sheet[1]/group[2]/field[@name='x']`` -> ``//field[@name='x']``.

    Every named step is kept, so a target inside an embedded sub-view
    (``field[@name='lines']/list[1]/field[@name='state']``) stays inside it
    instead of jumping to a same-named field of the main model.
    """
    if not LAST_NAMED_STEP.search(expr):
        return None
    alt = "//" + "//".join(f"{tag}[@name='{name}']" for tag, name in NAMED_STEP.findall(expr))
    return alt if alt != expr else None


def _prune_specs(combined, arch, label):
    """Return ``arch`` without the top-level specs that cannot be applied on
    ``combined`` (re-anchoring positional xpaths when possible)."""
    root = etree.fromstring(arch.encode())
    specs = list(root) if root.tag == "data" else [root]
    work = copy.deepcopy(combined)
    for spec in specs:
        if not isinstance(spec.tag, str):
            continue
        node = locate_node(work, spec)
        if node is None and spec.tag == "xpath":
            alt = _relaxed_expr(spec.get("expr", ""))
            if alt:
                probe = copy.deepcopy(spec)
                probe.set("expr", alt)
                if locate_node(work, probe) is not None:
                    _logger.info("%s: re-anchored %s -> %s", label, spec.get("expr"), alt)
                    spec.set("expr", alt)
                    node = True
        if node is None:
            _logger.warning("%s: dropped spec, target not found: %s", label, spec.get("expr") or spec.tag)
            if spec.getparent() is None:
                return "<data/>"
            spec.getparent().remove(spec)
            continue
        wrapper = etree.Element("data")
        wrapper.append(copy.deepcopy(spec))
        try:
            work = apply_inheritance_specs(work, wrapper)
        except Exception as exc:  # noqa: BLE001
            _logger.warning("%s: dropped spec %s: %s", label, spec.get("expr") or spec.tag, exc)
            if spec.getparent() is None:
                return "<data/>"
            spec.getparent().remove(spec)
    return etree.tostring(root, encoding="unicode")


def _strip_field(arch, field_name, nested_only, label):
    """Remove ``<field name=field_name>`` nodes (only those inside embedded
    sub-views when the field is valid on the view's own model) and the xpath
    specs targeting it."""
    root = etree.fromstring(arch.encode())
    removed = 0
    for node in list(root.iter("field")):
        if node.get("name") != field_name or node.getparent() is None:
            continue
        if nested_only and not any(a.tag in SUBVIEW_TAGS for a in node.iterancestors()):
            continue
        node.getparent().remove(node)
        removed += 1
    if not nested_only:
        for node in list(root.iter("xpath")):
            if f"@name='{field_name}'" in node.get("expr", "") and node.getparent() is not None:
                node.getparent().remove(node)
                removed += 1
    _logger.warning("%s: stripped field %s (%s nodes)", label, field_name, removed)
    return etree.tostring(root, encoding="unicode"), removed


def _load_base_archs():
    path = os.path.join(os.path.dirname(__file__), BASE_ARCHS_FILE)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write(cr, view_id, arch_db, active):
    cr.execute(
        "UPDATE ir_ui_view SET arch_db = %s, active = %s WHERE id = %s",
        (json.dumps(arch_db), active, view_id),
    )


def _repair_view(cr, env, view, xmlid, base_arch_db):
    label = f"{xmlid} ({view.id})"
    cr.execute("SELECT arch_db FROM ir_ui_view WHERE id = %s", (view.id,))
    current = cr.fetchone()[0] or {}
    source = base_arch_db or current
    fallback = next((a for a in source.values() if a), None)
    if not fallback:
        return False

    # The parent as the overlay will see it: the root view combined with
    # every *active* overlay (this one is inactive, so it is not included).
    combined = view.inherit_id._get_combined_arch()
    model_fields = env[view.model]._fields

    arch_db = {}
    for lang in set(current) | set(source):
        arch = source.get(lang) or fallback
        arch = _apply_renames(view.model, arch)
        arch_db[lang] = _prune_specs(combined, arch, f"{label}[{lang}]")

    for _round in range(MAX_VALIDATION_ROUNDS):
        try:
            with cr.savepoint():
                _write(cr, view.id, arch_db, True)
                env.invalidate_all()
                env["ir.ui.view"].browse(view.id)._check_xml()
            _logger.info("%s: Studio overlay repaired and reactivated", label)
            return True
        except Exception as exc:  # noqa: BLE001
            env.invalidate_all()
            match = MISSING_FIELD.search(str(exc))
            if not match:
                _logger.warning("%s: left inactive, still invalid: %s", label, exc)
                return False
            field_name, field_model = match.groups()
            # Missing on a sub-view's comodel: only strip it inside embedded
            # sub-views, the same name may be valid on the main model.
            nested_only = field_model != view.model and field_name in model_fields
            total = 0
            for lang, arch in arch_db.items():
                arch_db[lang], removed = _strip_field(arch, field_name, nested_only, f"{label}[{lang}]")
                total += removed
            if not total:
                _logger.warning("%s: left inactive, cannot strip %s: %s", label, field_name, exc)
                return False
    _logger.warning("%s: left inactive after %s validation rounds", label, MAX_VALIDATION_ROUNDS)
    return False


def _repair_studio_overlays(cr, env):
    base_archs = _load_base_archs()
    cr.execute("""
        SELECT v.id, imd.module || '.' || imd.name
          FROM ir_ui_view v
          JOIN ir_model_data imd ON imd.model = 'ir.ui.view' AND imd.res_id = v.id
         WHERE imd.module = 'studio_customization'
           AND v.active IS NOT TRUE
           AND v.type != 'qweb'
           AND v.inherit_id IS NOT NULL
           AND v.mode = 'extension'
         ORDER BY v.priority, v.id
    """)
    rows = cr.fetchall()
    repaired = []
    for view_id, xmlid in rows:
        view = env["ir.ui.view"].browse(view_id)
        try:
            ok = _repair_view(cr, env, view, xmlid, base_archs.get(xmlid))
        except Exception:  # noqa: BLE001
            _logger.warning("%s (%s): repair aborted", xmlid, view_id, exc_info=True)
            env.invalidate_all()
            ok = False
        if ok:
            repaired.append(xmlid)
    _logger.info(
        "Studio overlays: %s of %s inactive overlays reactivated", len(repaired), len(rows)
    )


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _repair_studio_overlays(cr, env)
