# -*- coding: utf-8 -*-
# © 2021 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'MRP Cost Report',
    'version': '12.0.1.0.0',
    'author': 'Morwi Encoders Consulting SA DE CV',
    'category': 'Manufacture',
    'website': 'http://www.morwi.mx/',
    'license': 'LGPL-3',
    'summary': 'MRP Cost Report Analysis',
    'depends': [
        'sale',
        'mrp_workorder',
        'mrp_account',
        'mrp_account_workorder_v2',
    ],
    'data': [
        'security/ir.model.access.csv',
  #      'report/manufacture_cost_report.xml',
    ]
}
