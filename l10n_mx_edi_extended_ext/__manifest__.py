# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Descripciones especifica CE',
    'version': '15.01',
    'category': 'Accounting/Localizations/EDI',
    'summary': 'Agrega campos para descripciones especificas en los productos',
    'depends': [
        'l10n_mx_edi_40',
        'l10n_mx_edi_extended_40',
    ],
    'data': [
        'security/ir.model.access.csv',
#        'data/4.0/cfdi.xml',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
