# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models
from odoo.fields import Domain


class ProductProduct(models.Model):
    _inherit = "product.product"

    # def _get_domain_locations_new(self, location_ids,
    #                               company_id=False, compute_child=True):
    #     domain_quant_loc, domain_move_in_loc, domain_move_out_loc = super(
    #         ProductProduct, self)._get_domain_locations_new(
    #         location_ids,
    #         company_id,
    #         compute_child)
    #     locations = self.env['stock.location'].browse(location_ids)
    #     operator = compute_child and 'child_of' or 'in'
    #     hierarchical_locations = (
    #         locations if operator == 'child_of' else locations.browse())
    #     wrong_locations = []
    #     for location in hierarchical_locations:
    #         # Pre-Production
    #         wrong_locations.append(
    #             location.warehouse_id.sam_loc_id.id)
    #         # Post-Production
    #         wrong_locations.append(
    #             location.warehouse_id.pbm_loc_id.id)
    #     domain_quant_loc.append(
    #         ('location_id', 'not in', wrong_locations))
    #     domain_move_in_loc.append(
    #         ('location_dest_id', 'not in', wrong_locations))
    #     domain_move_out_loc.append(
    #         ('location_id', 'not in', wrong_locations))
    #     return (domain_quant_loc, domain_move_in_loc, domain_move_out_loc)


    def _get_domain_locations_new(self, *args, **kwargs):
        res = super()._get_domain_locations_new(*args, **kwargs)
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = res

        location_ids = args[0] if args else kwargs.get('location_ids', [])
        compute_child = kwargs.get('compute_child', True)

        locations = self.env['stock.location'].browse(location_ids)

        wrong_locations = []
        for location in locations:
            if location.warehouse_id.sam_loc_id:
                wrong_locations.append(location.warehouse_id.sam_loc_id.id)
            if location.warehouse_id.pbm_loc_id:
                wrong_locations.append(location.warehouse_id.pbm_loc_id.id)

        if wrong_locations:
            # Asegurar que todo sea Domain
            if isinstance(domain_quant_loc, list):
                domain_quant_loc = Domain(domain_quant_loc)
            if isinstance(domain_move_in_loc, list):
                domain_move_in_loc = Domain(domain_move_in_loc)
            if isinstance(domain_move_out_loc, list):
                domain_move_out_loc = Domain(domain_move_out_loc)

            domain_quant_loc &= Domain('location_id', 'not in', wrong_locations)
            domain_move_in_loc &= Domain('location_dest_id', 'not in', wrong_locations)
            domain_move_out_loc &= Domain('location_id', 'not in', wrong_locations)

        return (domain_quant_loc, domain_move_in_loc, domain_move_out_loc)

