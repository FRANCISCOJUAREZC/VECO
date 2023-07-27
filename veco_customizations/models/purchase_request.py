# -*- coding: utf-8 -*-
# Copyright 2019 Morwi Encoders Consulting SA de CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import pytz

from odoo import api, fields, models


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    approval_date = fields.Date(
        compute="_compute_approval_date",
        store=True,
    )

    @api.depends('state')
    def _compute_approval_date(self):
        MailTrackingValue = self.env['mail.tracking.value'].sudo()
        Translation = self.env['ir.translation']
        for request in self:
            approved_state = 'Aprobada'
            field_stage = self.env['ir.model.fields']._get(
                self._name, "state")
            tracking_value = MailTrackingValue.search([
                ('mail_message_id', 'in', request.message_ids.ids),
                ('field', '=', field_stage.id),
                ('new_value_char', '=', approved_state)], order="id desc", limit=1)
            if tracking_value:
                date = tracking_value.mail_message_id.date.astimezone(
                    pytz.timezone('America/Mexico_City')).strftime(
                    '%Y-%m-%d')
                request.approval_date = fields.Date.from_string(date)
            else:
                request.approval_date = False
