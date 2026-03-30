# -*- coding: utf-8 -*-
##############################################################################
#                 @author IT Admin
#
##############################################################################

{
    'name': 'Adenda OC',
    'version': '19.0.15.02',
    'description': ''' Agrega nodo de Adenda con la OC
    ''',
    'category': 'Accounting',
    'author': 'IT Admin',
    'website': 'odoo.itadmin.com.mx',
    'depends': [
        'sale', 'l10n_mx_edi',
    ],
    'data': [
        #'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
	],
    'application': False,
    'installable': True,
    'license': 'AGPL-3',
}
