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
    ('button', 'action_open_project'),
]

# Fields whose names appear in expression attributes (readonly/invisible/etc.)
# but no longer exist on the model in v19.
INVALID_EXPR_FIELDS = []

EXPR_ATTRS = ('readonly', 'invisible', 'required', 'column_invisible', 'domain')


def _scrub_expression(expr, field_name):
    """Remove sub-expressions that reference *field_name* from *expr*."""
    fn = re.escape(field_name)
    patterns = [
        r'\s+or\s+\([^)]*\bnot\s+' + fn + r'[^)]*\)',
        r'\s+or\s+\([^)]*\b' + fn + r'[^)]*\)',
        r'\s+and\s+not\s+' + fn + r'\b',
        r'\s+and\s+' + fn + r'\b',
        r'\s+or\s+not\s+' + fn + r'\b',
        r'\s+or\s+' + fn + r'\b',
        r'\bnot\s+' + fn + r'\b',
        fn,
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, '', expr)
        if cleaned != expr:
            cleaned = re.sub(r'^\s*(and|or)\s+', '', cleaned.strip())
            cleaned = re.sub(r'\s+(and|or)\s*$', '', cleaned.strip())
            return cleaned.strip()
    return expr


def _clean_arch(xml_str):
    """Remove invalid nodes and fix stale field references in expression attributes."""
    try:
        tree = etree.fromstring(xml_str.encode())
    except etree.XMLSyntaxError as e:
        _logger.warning("Could not parse arch XML: %s", e)
        return xml_str, 0

    changes = 0

    for tag, name in INVALID_NODES:
        selector = (
            f"//{tag}[@name='{name}']" if tag != '*'
            else f"//*[@name='{name}']"
        )
        for node in tree.xpath(selector):
            node.getparent().remove(node)
            changes += 1
            _logger.debug("Removed <%s name='%s'>", tag, name)

    for field_name in INVALID_EXPR_FIELDS:
        for attr in EXPR_ATTRS:
            for node in tree.xpath(f"//*[contains(@{attr}, '{field_name}')]"):
                original = node.get(attr)
                fixed = _scrub_expression(original, field_name)
                if fixed != original:
                    node.set(attr, fixed)
                    changes += 1

    return etree.tostring(tree, encoding="unicode"), changes


def migrate(cr, version):
    """Remove invalid button/field nodes from mrp.production views before v19
    strict validation runs.

    ``action_open_project`` was removed from mrp.production in v19 but the
    button may still be present in views stored in the database.
    """
    all_names = [name for _, name in INVALID_NODES] + INVALID_EXPR_FIELDS
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
            _logger.info("Applied %s fix(es) to view id=%s.", total_changes, view_id)
        else:
            _logger.warning(
                "Pattern matched but nothing fixable for view id=%s — "
                "manual review needed.", view_id
            )
