# -*- coding: utf-8 -*-
{
    'name': 'Kárdex de inventario',
    'summary': 'Reporte kárdex de inventario.',
    'description': 'Generación de kárdex de inventario por ubicaciones y productos.',
    'version': '14.0.1',
    'category': 'Inventario',
    'author': 'Sistemas Grupo Ley',
    'website': "todoo.grupoley.com.mx",
    'depends': ['base', 'stock', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'security/stock_kardex_report_rules.xml',
        'views/stock_kardex_report_views.xml',
        'wizard/stock_kardex_report_wizard_view.xml',
        'reports/stock_kardex_report_pdf.xml',
        'reports/stock_kardex_report_xlsx.xml'
    ],
    'license': 'AGPL-3',
}
