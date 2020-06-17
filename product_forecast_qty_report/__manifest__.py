# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Product Forecast Qty Report',
    'version': '12.0.1.0.0',
    'author': 'Morwi Encoders Consulting SA DE CV',
    'category': 'Inventory',
    'website': 'http://www.morwi.mx/',
    'license': 'LGPL-3',
    'summary': 'Show the forecasted qty detail',
    'depends': ['stock_product_available_qty'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/product_forecast_report_views.xml',
    ]
}
