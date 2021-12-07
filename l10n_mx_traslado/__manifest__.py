# -*- coding: utf-8 -*-
##############################################################################
#                 @author IT Admin
#
##############################################################################

{
    'name': 'CFDI Traslado EE',
    'version': '12.03',
    'description': ''' Agrega campos para generar CFDI de tipo traslado con el complemento de carta porte.
    ''',
    'category': 'Accounting',
    'author': 'IT Admin',
    'website': 'www.itadmin.com.mx',
    'depends': [
        'account', 'l10n_mx_catalogos', 'l10n_mx_edi_external_trade', 'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/invoice_report.xml',
        'views/factura_traslado_view.xml',
        'views/product_view.xml',
        'views/res_company_view.xml',
        'data/ir_sequence_data.xml',
        'views/res_partner_view.xml',
        'data/mail_template_data.xml',
        'views/stock_picking_view.xml',
        'views/autotransporte_view.xml',
	],
    'application': False,
    'installable': True,
}
