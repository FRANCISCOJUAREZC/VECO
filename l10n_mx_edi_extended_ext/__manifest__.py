# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Descripciones especifica CE',
    'version': '19.1.0',
    'category': 'Accounting/Localizations/EDI',
    'summary': 'Agrega campos para descripciones especificas en los productos',
    'depends': [
        'l10n_mx_edi',
    ],
    'data': [
        'data/cfdi.xml',
        'security/ir.model.access.csv',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
