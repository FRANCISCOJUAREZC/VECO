# -*- coding: utf-8 -*-
# © 2020 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models
from odoo.osv import expression


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
        # Ejecutamos el super de forma flexible
        res = super(ProductProduct, self)._get_domain_locations_new(*args, **kwargs)
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = res

        # Extraemos los valores de los argumentos sin importar la posición
        # location_ids suele ser el primer argumento en args o estar en kwargs
        location_ids = args[0] if args else kwargs.get('location_ids', [])
        compute_child = kwargs.get('compute_child', True)

        locations = self.env['stock.location'].browse(location_ids)
        operator = 'child_of' if compute_child else 'in'
        
        # Filtrado de locaciones (tu lógica personalizada)
        hierarchical_locations = locations if operator == 'child_of' else locations.browse()
        wrong_locations = []
        for location in hierarchical_locations:
            if location.warehouse_id.sam_loc_id:
                wrong_locations.append(location.warehouse_id.sam_loc_id.id)
            if location.warehouse_id.pbm_loc_id:
                wrong_locations.append(location.warehouse_id.pbm_loc_id.id)

        # Aplicamos los filtros a los dominios obtenidos del super
        # In Odoo 17+, domains may be DomainCondition objects instead of lists
        if wrong_locations:
            def to_list(dom):
                if isinstance(dom, list):
                    return dom
                try:
                    return list(dom)
                except TypeError:
                    return [dom]

            domain_quant_loc = expression.AND([to_list(domain_quant_loc), [('location_id', 'not in', wrong_locations)]])
            domain_move_in_loc = expression.AND([to_list(domain_move_in_loc), [('location_dest_id', 'not in', wrong_locations)]])
            domain_move_out_loc = expression.AND([to_list(domain_move_out_loc), [('location_id', 'not in', wrong_locations)]])

        return (domain_quant_loc, domain_move_in_loc, domain_move_out_loc)

