# -*- coding: utf-8 -*-
# Copyright 2026 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
"""Rebuild the "Estado de Resultados Veco" accounting report for Odoo 19.

In Odoo 15 the report was the custom ``account.financial.html.report`` id 8
("Estado de Resultados - Veco (copia)", menu "Estado de Resultados V" under
Contabilidad > Informes, action 1468). The upgrade to Odoo 19 did not convert
it to ``account.report``: the report, its 43 lines, its action and its menu
were dropped. Only the action/menu of the long-deleted report id 6
(``account_reports.account_financial_html_report_action_6`` / ``..._menu_6``)
survived, archived and pointing to the removed ``account.financial.html.report``
model.

This script recreates the report from the production definition:

* lines with a domain (``account_id ilike <code>``, formula ``-sum``) become
  ``domain`` engine expressions with the same domain and subformula;
* lines with a formula between codes become ``aggregation`` expressions;
* the Odoo 15 ``level`` is kept as ``hierarchy_level`` and lines grouped by
  account stay grouped (foldable);
* a client action and a menu under Contabilidad > Informes > Estados financieros
  are created, and the broken leftovers of report id 6 are removed.

Records get ``noupdate`` xmlids in ``veco_customizations`` so the script is
idempotent and they survive module updates.
"""

import logging
import re

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

MODULE = "veco_customizations"
XMLID_REPORT = "account_report_estado_resultados_veco"
XMLID_ACTION = "action_account_report_estado_resultados_veco"
XMLID_MENU = "menu_account_report_estado_resultados_veco"

REPORT_NAME = "Estado de Resultados Veco"
MENU_NAME = "Estado de Resultados V"

OBSOLETE_XMLIDS = [
    "account_reports.account_financial_html_report_menu_6",
    "account_reports.account_financial_html_report_action_6",
]

# (code, name, hierarchy_level, engine, formula, groupby account)
# domain engine: formula is the account code matched with ``ilike``.
# aggregation engine: formula uses line codes, ``.balance`` is added below.
LINES = [
    ("ER_VT", "VENTAS", 0, "domain", "404", True),
    ("ER_MOP", "MANO DE OBRA PAGADA", 1, "aggregation", "ER_TMOPGOP1+ER_TMOPGOP2", False),
    ("ER_TMOPGOP1", "T MANO OBRA PAGADA P1", 1, "aggregation", "ER_MOE+ER_TEDE+ER_TETE+ER_CSE", False),
    ("ER_MOE", "MANO DE OBRA EQUIPO", 3, "domain", "511.0001.01.00", False),
    ("ER_TEDE", "T.EXTRA DOBLE EQUIPO", 3, "domain", "511.0001.70.00", False),
    ("ER_TETE", "T.EXTRA TRIPLE EQUIPO", 3, "domain", "511.0001.71.00", False),
    ("ER_CSE", "CARGA SOCIAL EQUIPO", 3, "aggregation", "ER_TMOE-ER_MOE-ER_TEDE-ER_TETE-ER_TMOFE", False),
    ("ER_TMOPGOP2", "T MANO OBRA PAGADA P2", 1, "aggregation", "ER_MOF+ER_TEDF+ER_TETF+ER_CSF", False),
    ("ER_MOF", "MANO DE OBRA FILTROS", 3, "domain", "511.0002.01.00", False),
    ("ER_TEDF", "T.ETRA DOBLE FILTRO", 3, "domain", "511.0002.70.00", False),
    ("ER_TETF", "T.EXTRA TRIPLE FILTRO", 3, "domain", "511.0002.71.00", False),
    ("ER_CSF", "CARGA SOCIAL FILTRO", 3, "aggregation", "ER_TMOF-ER_MOF-ER_TEDF-ER_TETF-ER_TMOFF", False),
    ("ER_MOPAGP1", "T MO PAGADA P1", 2, "aggregation", "ER_MOE+ER_TEDE+ER_TETE+ER_CSE", False),
    ("ER_TMOFE", "T MO FACT OP P1", 2, "domain", "511.0001.99.00", False),
    ("ER_MOFVSPP1", "T MO FAC SIN AFECTAR OP P1", 1, "aggregation", "ER_MOPAGP1+ER_TMOFE", False),
    ("ER_MOPAGP2", "T MO PAGADA P2", 0, "aggregation", "ER_MOF+ER_TEDF+ER_TETF+ER_CSF", False),
    ("ER_TMOFF", "T MO FACT OP P2", 2, "domain", "511.0002.99.00", False),
    ("ER_MOFVSPP2", "T MO FAC SIN AFECTAR OP P2", 1, "aggregation", "ER_MOPAGP2+ER_TMOFF", False),
    ("ER_TMOE", "TMANO OBRA P1", 2, "domain", "511.0001", False),
    ("ER_TMOF", "T MANO OBRA P2", 1, "domain", "511.0002", False),
    ("ER_MO", "MANO DE OBRA", 0, "domain", "511", True),
    ("ER_GIF", "GASTOS INDIRECTOS", 3, "domain", "520", True),
    ("ER_CTO", "COSTO DE VENTAS", 3, "domain", "540", True),
    ("ER_CTODVI", "COSTO SERVICIOS DVI", 3, "domain", "550", True),
    ("ER_CTOVTA", "T COSTO DE VENTAS", 1, "aggregation", "ER_MO+ER_GIF+ER_CTO+ER_CTODVI", False),
    ("ER_UB", "UTILIDAD BRUTA", 1, "aggregation", "ER_VT+ER_CTOVTA", False),
    ("ER_GV", "GASTOS DE VENTA", 3, "domain", "600", True),
    ("ER_MM", "MEDIACION MERCANTIL", 3, "domain", "600.0002.59.00", False),
    ("ER_TGV", "T GASTOS DE VENTA", 1, "aggregation", "ER_GV-ER_MM", False),
    ("ER_GA", "GASTOS DE ADMINISTRACION", 3, "domain", "610", True),
    ("ER_TGO", "T GASTOS OPERACION", 1, "aggregation", "ER_GV+ER_GA", False),
    ("ER_UOP", "UTILIDAD OPERATIVA", 1, "aggregation", "ER_UB+ER_TGO", False),
    ("ER_PF", "PRODUCTOS FINANCIEROS", 3, "domain", "414", False),
    ("ER_GC", "GANANCIA CAMBIARIA", 3, "domain", "490", False),
    ("ER_GF", "GASTOS FINANCIEROS", 3, "domain", "620", False),
    ("ER_PC", "PERDIDA CAMBIARIA", 3, "domain", "690", False),
    ("ER_FINT", "GASTOS INT FINANCIAMIENTO", 1, "aggregation", "ER_PF+ER_GC+ER_GF+ER_PC", False),
    ("ER_VTAAF", "VENTA ACTIVO FIJO", 3, "domain", "430", False),
    ("ER_OP", "OTROS PRODUCTOS", 3, "domain", "411", False),
    ("ER_DP", "DIFERENCIAS EN PRECIOS", 3, "domain", "651", False),
    ("ER_OG", "OTROS GASTOS", 3, "domain", "650", False),
    ("ER_OIG", "OTROS INGRESOS Y GASTOS", 1, "aggregation", "ER_VTAAF+ER_OP+ER_DP+ER_OG", False),
    ("ER_RAI", "RESULTADO ANTES DE IMPUESTOS", 1, "aggregation", "ER_UOP+ER_FINT+ER_OIG", False),
]

CODE_RE = re.compile(r"\bER_[A-Z0-9]+\b")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if "account.report" not in env or not env.ref("account_reports.action_account_report_pl", False):
        _logger.warning("account_reports is not installed, Estado de Resultados Veco not created")
        return
    report = env.ref(f"{MODULE}.{XMLID_REPORT}", raise_if_not_found=False)
    if not report:
        report = _create_report(env)
    action = env.ref(f"{MODULE}.{XMLID_ACTION}", raise_if_not_found=False)
    if not action:
        action = _create_action(env, report)
    if not env.ref(f"{MODULE}.{XMLID_MENU}", raise_if_not_found=False):
        _create_menu(env, action)
    _remove_obsolete(env)


def _line_vals(sequence, code, name, level, engine, formula, groupby):
    if engine == "domain":
        expression = {
            "label": "balance",
            "engine": "domain",
            "formula": repr([("account_id", "ilike", formula)]),
            "subformula": "-sum",
        }
    else:
        expression = {
            "label": "balance",
            "engine": "aggregation",
            "formula": CODE_RE.sub(lambda m: m.group(0) + ".balance", formula).replace("+", " + ").replace("-", " - "),
        }
    vals = {
        "sequence": sequence,
        "code": code,
        "name": name,
        "hierarchy_level": level,
        "expression_ids": [(0, 0, expression)],
    }
    if groupby:
        vals.update(groupby="account_id", foldable=True)
    return vals


def _create_report(env):
    report = env["account.report"].create({
        "name": REPORT_NAME,
        "availability_condition": "always",
        "filter_date_range": True,
        "filter_period_comparison": True,
        "filter_unfold_all": True,
        "filter_journals": True,
        "filter_multi_company": "selector",
        "default_opening_date_filter": "this_year",
        "column_ids": [(0, 0, {"name": "Saldo", "expression_label": "balance", "figure_type": "monetary"})],
        "line_ids": [
            (0, 0, _line_vals((index + 1) * 10, *line))
            for index, line in enumerate(LINES)
        ],
    })
    _xmlid(env, XMLID_REPORT, report)
    _logger.info("Report %s created (id %s) with %s lines", REPORT_NAME, report.id, len(report.line_ids))
    return report


def _create_action(env, report):
    action = env["ir.actions.client"].create({
        "name": REPORT_NAME,
        "tag": "account_report",
        "context": repr({"report_id": report.id}),
    })
    _xmlid(env, XMLID_ACTION, action)
    _logger.info("Client action %s created for report %s", action.id, report.id)
    return action


def _create_menu(env, action):
    pl_menu = env.ref("account_reports.menu_action_account_report_profit_and_loss")
    menu = env["ir.ui.menu"].create({
        "name": MENU_NAME,
        "parent_id": env.ref("account.account_reports_legal_statements_menu").id,
        "action": f"ir.actions.client,{action.id}",
        "sequence": pl_menu.sequence + 1,
        "group_ids": [(6, 0, pl_menu.group_ids.ids)],
    })
    _xmlid(env, XMLID_MENU, menu)
    _logger.info("Menu %s created (id %s)", MENU_NAME, menu.id)


def _remove_obsolete(env):
    """Delete the archived menu/action of the removed report id 6."""
    for xmlid in OBSOLETE_XMLIDS:
        record = env.ref(xmlid, raise_if_not_found=False)
        if record:
            _logger.info("Removing obsolete %s (%s %s)", xmlid, record._name, record.id)
            record.with_context(active_test=False).unlink()


def _xmlid(env, name, record):
    env["ir.model.data"].create({
        "module": MODULE,
        "name": name,
        "model": record._name,
        "res_id": record.id,
        "noupdate": True,
    })
