# -*- coding: utf-8 -*-
# Copyright 2022 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import xmlrpc.client

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['res.partner'].search(
        [('parent_id', '!=', False)])._compute_display_name()
    url = 'https://vecomx-staging-5744626.dev.odoo.com/'
    db = "vecomx-staging-5744626"
    username = 'admin'
    password = "admin"
    import ipdb; ipdb.set_trace()
    info = xmlrpc.client.ServerProxy(
        'https://vecomx-staging-5744626.dev.odoo.com/start').start()
    url, db, username, password = info['host'], info['database'], info['user'], info['password']

    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    common.version()
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    timelines = env['mrp.workcenter.productivity'].search(
        [('workforce_entry_id', '=', False)])
    AccountMove = env['account.move']
    for timeline in timelines:
        time_v12 = models.execute_kw(
            db, uid, password, 'mrp.workcenter.productivity', 'search_read',
            [[['id', '=', timeline.id]]],
            {'fields': ['name', 'workforce_entry_id']})
        move = AccountMove.browse(
            time_v12['workforce_entry_id'])
        move.write({
            'mrp_timeline_id': timeline.id,
        })
        move.line_ids.write({
            'mrp_timeline_id': timeline.id,
        })
