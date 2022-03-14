# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Xunnel Bank',
    'summary': '''
        Use Xunnel Bank to retrieve bank statements.
    ''',
    'version': '15.0.1.0.0',
    'author': 'Jarsa Sistemas,Vauxoo',
    'category': 'Accounting',
    'website': 'http://www.xunnel.com',
    'license': 'LGPL-3',
    'depends': [
        'account_accountant',
        'account_asset',
        'account_online_synchronization',
    ],
    'demo': [
    ],
    'data': [
        # WiZARDS
        'wizards/wizard_change_date.xml',
        'wizards/wizard_download_bank_accounts.xml',
        'wizards/wizard_set_up_connection_token.xml',

        # DATA
        'data/config_parameters.xml',
        'data/images_library.xml',
        'data/xunnel_actions.xml',

        # SECURITY
        'security/ir.model.access.csv',

        # VIEWS
        'views/account_online_sync.xml',
        'views/accountant_dashboard.xml',
        'views/xunnel_menuitems.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/account_xunnel/static/src/js/add_account_manager.js',
            '/account_xunnel/static/src/css/backend.css',
            '/account_xunnel/static/src/js/synchronized_account.js',
        ],
        'web.assets_qweb': [
            '/account_xunnel/static/src/xml/add_account_manager.xml',
        ],
    },
    'installable': True,
}
