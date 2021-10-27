# -*- coding: utf-8 -*-
{
    'name': "Plan de producción",

    'description': """
        This module creates production plan from sale and mrp
    """,

    'author': "Morwi Econders",
    'website': "http://www.morwi.mx",
    'category': 'MRP',
    'version': '0.1',
    'depends': ['base','sale','mrp','product'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_plan.xml',
        'wizard/production_plan_wizard_view.xml',
        'views/mrp_views.xml',
    ],
}
