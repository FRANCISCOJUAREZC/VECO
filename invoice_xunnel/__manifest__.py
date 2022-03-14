# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Xunnel Invoice',
    'summary': '''
        Use Xunnel Invoice to retrieve invoices from SAT.
    ''',
    'version': '15.0.1.0.0',
    'author': 'Jarsa Sistemas, Vauxoo',
    'category': 'Accounting',
    'website': 'http://www.xunnel.com',
    'license': 'LGPL-3',
    'depends': [
        'account_xunnel',
        'documents',
        'l10n_mx_edi',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/documents_views.xml',
        'wizards/documents.xml',
        'views/xunnel_menuitems.xml',
    ],
    'demo': [
        'demo/res_company.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/invoice_xunnel/static/src/css/style.css',
            '/invoice_xunnel/static/src/less/main.less',
            '/invoice_xunnel/static/src/lib/google_pretty_print.js',
            '/invoice_xunnel/static/src/lib/notify.min.js',
            '/invoice_xunnel/static/src/js/attach_xmls_org.js',
            '/invoice_xunnel/static/src/js/attach_xmls.js',
            '/invoice_xunnel/static/src/js/documents_inspector.js',
            '/invoice_xunnel/static/src/js/document_viewer.js',
            '/invoice_xunnel/static/src/js/documents_dashboard.js',
            ],
        'web.assets_qweb': [
            '/invoice_xunnel/static/src/xml/*.xml',
        ],
    },
    'installable': True,
}
