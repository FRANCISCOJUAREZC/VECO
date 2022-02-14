# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Base report xlsx",
    "summary": "Base module to create xlsx report",
    "author": "ACSONE SA/NV," "Creu Blanca," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/reporting-engine",
    "category": "Reporting",
    "version": "15.0.1.0.0",
    "development_status": "Production/Stable",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["xlsxwriter", "xlrd"]},
    "depends": ["base", "web"],
    "data": ["views/webclient_templates.xml"],
    'assets': {
        'web.assets_backend': [
                     ('include', 'web._assets_backend_helpers'),
                     ('include', 'web._assets_helpers'),
                     "/report_xlsx/static/src/js/report/action_manager_report.js",
            ],
            },
    "demo": ["demo/report.xml"],
    "installable": True,
}
