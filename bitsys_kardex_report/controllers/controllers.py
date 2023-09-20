# -*- coding: utf-8 -*-
# from odoo import http


# class BitsysKardexReport(http.Controller):
#     @http.route('/bitsys_kardex_report/bitsys_kardex_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bitsys_kardex_report/bitsys_kardex_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bitsys_kardex_report.listing', {
#             'root': '/bitsys_kardex_report/bitsys_kardex_report',
#             'objects': http.request.env['bitsys_kardex_report.bitsys_kardex_report'].search([]),
#         })

#     @http.route('/bitsys_kardex_report/bitsys_kardex_report/objects/<model("bitsys_kardex_report.bitsys_kardex_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bitsys_kardex_report.object', {
#             'object': obj
#         })
