# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    sync_button_visible = fields.Boolean(
        compute='_compute_sync_button_visible',
        store=True,)
    synchronized = fields.Boolean()

    @api.depends('state')
    def _compute_sync_button_visible(self):
        for production in self:
            sync_button_visible = False
            if (production.product_tracking == 'serial' and
                    production.state == 'to_close' and
                    production.name.endswith('001')):
                sync_button_visible = True
            production.sync_button_visible = sync_button_visible

    def action_confirm(self):
        self._check_company()
        for production in self:
            if production.bom_id:
                production.consumption = production.bom_id.consumption
            # In case of Serial number tracking, force the UoM to the UoM of product
            if production.product_tracking == 'serial' and production.product_uom_id != production.product_id.uom_id:
                production.write({
                    'product_qty': production.product_uom_id._compute_quantity(production.product_qty, production.product_id.uom_id),
                    'product_uom_id': production.product_id.uom_id
                })
                for move_finish in production.move_finished_ids.filtered(lambda m: m.product_id == production.product_id):
                    move_finish.write({
                        'product_uom_qty': move_finish.product_uom._compute_quantity(move_finish.product_uom_qty, move_finish.product_id.uom_id),
                        'product_uom': move_finish.product_id.uom_id
                    })
            ###### OVERRIDE to ensure the PC creation ######
            production.move_raw_ids.write({'procure_method': 'make_to_order'})
            (production.move_raw_ids | production.move_finished_ids)._action_confirm(merge=False)
            production.workorder_ids._action_confirm()
        # run scheduler for moves forecasted to not have enough in stock
        self.move_raw_ids._trigger_scheduler()
        self.picking_ids.filtered(
            lambda p: p.state not in ['cancel', 'done']).action_confirm()
        # Force confirm state only for draft production not for more advanced state like
        # 'progress' (in case of backorders with some qty_producing)
        self.filtered(lambda mo: mo.state == 'draft').state = 'confirmed'
        return True

    def prorate_workorder_times(self):
        principal_order = self[:1]
        qty_total = sum(self.mapped('product_qty'))
        to_unlink = self.env['mrp.workcenter.productivity']
        _logger.info(
            "Order: %s prorating times - Creating times", principal_order.name)
        for production in self[1:]:
            for workorder in principal_order.workorder_ids:
                current_wo = production.workorder_ids.filtered(
                    lambda wo: wo.workcenter_id == workorder.workcenter_id)
                to_unlink |= current_wo.time_ids
                for time in workorder.time_ids:
                    qty_to_split = (
                        time.duration / qty_total if not
                        principal_order.synchronized else time.duration)
                    new_time = time.copy({
                        'workorder_id': current_wo.id,
                        'workforce_entry_id': False,
                        'duration': qty_to_split,
                    })
                    new_time.write({'duration': qty_to_split})
        _logger.info(
            "Order: %s prorating times - Setting unit times",
            principal_order.name)
        for workorder in principal_order.workorder_ids:
            for time in workorder.time_ids:
                qty_to_split = time.duration / qty_total
                time.write({
                    'duration': qty_to_split,
                })
        times_wo_am = principal_order.workorder_ids.mapped('time_ids').filtered(
            lambda time: not time.workforce_entry_id)
        for time in times_wo_am:
            time.create_workforce_entry()
        _logger.info(
            "Order: %s prorating times - Unlinking Moves",
            principal_order.name)
        to_unlink.unlink()

    def action_prorate_data(self):
        self.ensure_one()
        if not self.name.endswith('001'):
            raise ValidationError(
                _('This action only can be executed from the first manufacture'
                    ' order (ending with 001.'))
        # Prorate materials
        _logger.info("Order: %s prorating materials", self.name)
        backorders = self.procurement_group_id.mrp_production_ids - self
        AccountMoveLine = self.env['stock.move.line']
        for backorder in backorders:
            for move in backorder.move_raw_ids:
                # shared_vals = {
                #     'move_id': move.id,
                #     'product_id': move.product_id.id,
                #     'location_id': move.location_id.id,
                #     'location_dest_id': move.location_dest_id.id,
                #     'product_uom_qty': 0,
                #     'product_uom_id': move.product_uom.id,
                #     'lot_id': False,
                #     'company_id': move.company_id.id,
                #     'qty_done': move.product_uom_qty,
                # }
                # move.move_line_ids.unlink()
                # AccountMoveLine.create(shared_vals)
                for sml in move.move_line_ids:
                    sml.qty_done = sml.product_uom_qty
        for move in self.move_raw_ids:
            for sml in move.move_line_ids:
                sml.qty_done = sml.product_uom_qty
        # Prorate Times
        _logger.info("Order: %s prorating times", self.name)
        (self + backorders).prorate_workorder_times()
        self.synchronized = True
