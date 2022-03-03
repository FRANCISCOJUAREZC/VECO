# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Account Partner Budget',
    'version': '15.0.1.0.0',
    'author': 'Morwi Encoders Consulting SA DE CV',
    'category': 'Accounting',
    'website': 'http://www.morwi.mx/',
    'license': 'LGPL-3',
    'summary': '''This module allows to add a partner into the budget lins
     to track analytic lines by this field''',
    'depends': [
        'account_budget',
    ],
    'data': [
        'views/account_budget_views.xml',
        'views/account_analytic_line_views.xml',
    ]
}
