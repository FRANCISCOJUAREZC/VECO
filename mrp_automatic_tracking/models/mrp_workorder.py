# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models
from odoo.tools import float_compare


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    def _create_checks(self):
        """If not the manufacture order has the boolean set_manual_tracking
         checked is not necessary the quality checks to record
         the lots / serial no for cosnumed materials, so this checks
         are deleted"""
        res = super(MrpWorkOrder, self)._create_checks()
        for rec in self:
            if not rec.production_id.set_manual_tracking:
                rec.check_ids.unlink()
                rec.write({'is_last_step': True})
        return res

    def _generate_lot_ids(self):
        """If not the manufacture order has the boolean set_manual_tracking
         checked is not necessary the quality checks to record
         the lots / serial no for cosnumed materials, so this checks
         are deleted"""
        self.ensure_one()
        if self.production_id.set_manual_tracking:
            return super(MrpWorkOrder, self)._generate_lot_ids()
        return True
