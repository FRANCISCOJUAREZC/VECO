# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'MRP Account Workorder',
    'version': '15.0.1.0.0',
    'author': 'Morwi Encoders Consulting SA DE CV',
    'category': 'Manufacture',
    'website': 'http://www.morwi.mx/',
    'license': 'LGPL-3',
    'summary': '''Create Journal Entries for worforce''',
    'depends': ['mrp_account', 'mrp_workorder'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_warehouse_views.xml',
        'views/mrp_workorder_views.xml',
    ],
}
