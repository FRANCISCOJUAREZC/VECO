# -*- coding: utf-8 -*-
{
    'name': "Reporte de Kardex",

    'summary': """
        El reporte de Kardex en Odoo es una herramienta esencial para el control de inventario en una empresa. 
        Proporciona una visión detallada y actualizada de los movimientos de entrada y salida de productos en un período específico.""",

    'author': "Bit Systems, S.A",
    'website': "https://bitsys.odoo.com/",
    'license': 'AGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory',
    'version': '15.0',
    'price': 49.99,
    'currency': 'USD',

    # any module necessary for this one to work correctly
    'depends': ['stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'report/action_report.xml', 
        'wizard/kardex_wizard_view.xml', 
    ],
    # only loaded in demonstration mode
    'images': ['static/description/banner.gif'], 

    'demo': [
        'demo/demo.xml',
    ],
}
