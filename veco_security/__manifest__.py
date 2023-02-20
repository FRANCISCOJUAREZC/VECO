# -*- coding: utf-8 -*-
# Copyright 2023 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Security Veco',
    'category': 'Hidden',
    'version': '15.0.1.0.0',
    'description': """
        Module to add security to Veco
        """,
    'summary': """
        Module to add security to Veco
        """,
    'depends': ['mrp', 'quality_control', 'quality_mrp'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
    ],
}
