# -*- coding: utf-8 -*-
# Copyright 2026 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json
import logging
import re
from lxml import etree

_logger = logging.getLogger(__name__)

# Nodes to remove entirely (tag, name-attribute value).
# Use '*' as tag to match any element.
INVALID_NODES = [
    ('button', 'action_delete_duplicates'),
    ('field',  'l10n_mx_edi_partner_address_complete'),
]

# Fields whose names appear in expression attributes (readonly/invisible/etc.)
# but no longer exist on the model in v19. Any sub-expression that contains
# one of these names will be surgically removed from the attribute value.
INVALID_EXPR_FIELDS = [
    'l10n_mx_edi_partner_address_complete',
]

EXPR_ATTRS = ('readonly', 'invisible', 'required', 'column_invisible', 'domain')


def _scrub_expression(expr, field_name):
    """Remove sub-expressions that reference *field_name* from *expr*.

    Handles the most common patterns produced by Odoo view authors:
      - ``or (something and not field_name)``
      - ``or (something and field_name)``
      - ``or not field_name``
      - ``and not field_name``
      - ``and field_name``
      - bare ``field_name``
    Returns the cleaned expression string.
    """
    fn = re.escape(field_name)
    patterns = [
        # or (... not field_name)  /  or (... field_name)
        r'\s+or\s+\([^)]*\bnot\s+' + fn + r'[^)]*\)',
        r'\s+or\s+\([^)]*\b' + fn + r'[^)]*\)',
        # and not field_name  /  and field_name
        r'\s+and\s+not\s+' + fn + r'\b',
        r'\s+and\s+' + fn + r'\b',
        # or not field_name  /  or field_name
        r'\s+or\s+not\s+' + fn + r'\b',
        r'\s+or\s+' + fn + r'\b',
        # standalone: not field_name  /  field_name
        r'\bnot\s+' + fn + r'\b',
        fn,
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, '', expr)
        if cleaned != expr:
            # Strip dangling operators left at the start/end
            cleaned = re.sub(r'^\s*(and|or)\s+', '', cleaned.strip())
            cleaned = re.sub(r'\s+(and|or)\s*$', '', cleaned.strip())
            return cleaned.strip()
    return expr


def _clean_arch(xml_str):
    """Remove invalid nodes and fix stale field references in expression attributes.

    Returns (new_xml_str, total_changes).
    """
    try:
        tree = etree.fromstring(xml_str.encode())
    except etree.XMLSyntaxError as e:
        _logger.warning("Could not parse arch XML: %s", e)
        return xml_str, 0

    changes = 0

    # 1. Remove entire nodes whose name= matches a known-invalid method/field.
    for tag, name in INVALID_NODES:
        selector = (
            f"//{tag}[@name='{name}']" if tag != '*'
            else f"//*[@name='{name}']"
        )
        for node in tree.xpath(selector):
            node.getparent().remove(node)
            changes += 1
            _logger.debug("Removed <%s name='%s'>", tag, name)

    # 2. Fix expression attributes that reference removed fields.
    for field_name in INVALID_EXPR_FIELDS:
        for attr in EXPR_ATTRS:
            for node in tree.xpath(f"//*[contains(@{attr}, '{field_name}')]"):
                original = node.get(attr)
                fixed = _scrub_expression(original, field_name)
                if fixed != original:
                    node.set(attr, fixed)
                    changes += 1
                    _logger.debug(
                        "Fixed @%s on <%s name='%s'>: %r → %r",
                        attr, node.tag, node.get('name', '?'), original, fixed,
                    )

    return etree.tostring(tree, encoding="unicode"), changes


def migrate(cr, version):
    """Clean stale view arches before v19 strict view validation runs.

    Covers two kinds of staleness left by modules upgraded without a full
    ``--update all``:
    - Entire nodes (buttons/fields) whose name no longer exists on the model.
    - Expression attributes (readonly/invisible/…) that reference removed fields.

    arch_db is stored as JSONB (dict keyed by language) in Odoo v17+.
    """
    all_names = (
        [name for _, name in INVALID_NODES] + INVALID_EXPR_FIELDS
    )
    conditions = " OR ".join(
        f"arch_db::text LIKE '%%{name}%%'" for name in all_names
    )
    cr.execute(f"SELECT id, name, arch_db FROM ir_ui_view WHERE {conditions}")
    rows = cr.fetchall()

    if not rows:
        _logger.info("No problematic views found — nothing to do.")
        return

    for view_id, view_name, arch_db in rows:
        _logger.info("Processing view id=%s name=%s", view_id, view_name)

        if isinstance(arch_db, str):
            arch_db = json.loads(arch_db)

        total_changes = 0
        new_arch_db = {}
        for lang, xml_str in arch_db.items():
            new_xml, changes = _clean_arch(xml_str)
            new_arch_db[lang] = new_xml
            total_changes += changes

        if total_changes:
            cr.execute(
                "UPDATE ir_ui_view SET arch_db = %s WHERE id = %s",
                (json.dumps(new_arch_db), view_id),
            )
            _logger.info(
                "Applied %s fix(es) to view id=%s.", total_changes, view_id
            )
        else:
            _logger.warning(
                "Pattern matched in arch text but nothing was fixable via xpath/regex "
                "for view id=%s — manual review needed.", view_id
            )
