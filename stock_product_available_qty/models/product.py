# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_domain_locations_new(self, location_ids,
                                  company_id=False, compute_child=True):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = super(
            ProductProduct, self)._get_domain_locations_new(location_ids,
                                                            company_id,
                                                            compute_child)
        locations = self.env['stock.location'].browse(location_ids)
        operator = compute_child and 'child_of' or 'in'
        hierarchical_locations = (
            locations if operator == 'child_of' else locations.browse())
        wrong_locations = []
        for location in hierarchical_locations:
            warehouse = location.get_warehouse()
            # Pre-Production
            wrong_locations.append(warehouse.sam_loc_id.id)
            # Post-Production
            wrong_locations.append(warehouse.pbm_loc_id.id)
            # Do not take care of output, pack & input locations in
            # quant domain
            wrong_locations.append(warehouse.wh_input_stock_loc_id.id)
            wrong_locations.append(warehouse.wh_output_stock_loc_id.id)
            wrong_locations.append(warehouse.wh_pack_stock_loc_id.id)
        domain_quant_loc.append(
            ('location_id', 'not in', wrong_locations))
        # domain_move_in_loc.append(
        #     ('location_dest_id', 'not in', wrong_locations))
        # domain_move_out_loc.append(
        #     ('location_id', 'not in', wrong_locations))
        return (domain_quant_loc, domain_move_in_loc, domain_move_out_loc)
