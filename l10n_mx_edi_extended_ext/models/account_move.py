# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools.sql import column_exists, create_column
from odoo.tools import float_round

import re
from collections import defaultdict

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _l10n_mx_edi_add_invoice_cfdi_values(self, cfdi_values):
        # EXTENDS 'l10n_mx_edi'
        self.ensure_one()

        if self.journal_id.l10n_mx_address_issued_id:
            cfdi_values['issued_address'] = self.journal_id.l10n_mx_address_issued_id

        super()._l10n_mx_edi_add_invoice_cfdi_values(cfdi_values)
        if cfdi_values.get('errors'):
            return

        cfdi_values['exportacion'] = self.l10n_mx_edi_external_trade_type or '01'

        # External Trade
        ext_trade_values = cfdi_values['comercio_exterior'] = {}
        if self.l10n_mx_edi_external_trade_type == '02':

            # Customer.
            customer_values = cfdi_values['receptor']
            customer = customer_values['customer']
            if customer_values['rfc'] == 'XEXX010101000':
                cfdi_values['receptor']['num_reg_id_trib'] = customer.vat
                # A value must be registered in the ResidenciaFiscal field when information is registered in the
                # NumRegIdTrib field.
                cfdi_values['receptor']['residencia_fiscal'] = customer.country_id.l10n_mx_edi_code

            ext_trade_values['receptor'] = {
                **cfdi_values['receptor'],
                'curp': customer.l10n_mx_edi_curp,
                'calle': customer.street_name,
                'numero_exterior': customer.street_number,
                'numero_interior': customer.street_number2,
                'colonia': customer.l10n_mx_edi_colony_code,
                'localidad': customer.l10n_mx_edi_locality_id.code,
                'municipio': customer.city_id.l10n_mx_edi_code,
                'estado': customer.state_id.code,
                'pais': customer.country_id.l10n_mx_edi_code,
                'codigo_postal': customer.zip,
            }

            # Supplier.
            supplier_values = cfdi_values['emisor']
            supplier = supplier_values['supplier']
            ext_trade_values['emisor'] = {
                'curp': supplier.l10n_mx_edi_curp,
                'calle': supplier.street_name,
                'numero_exterior': supplier.street_number,
                'numero_interior': supplier.street_number2,
                'colonia': supplier.l10n_mx_edi_colony_code,
                'localidad': supplier.l10n_mx_edi_locality_id.code,
                'municipio': supplier.city_id.l10n_mx_edi_code,
                'estado': supplier.state_id.code,
                'pais': supplier.country_id.l10n_mx_edi_code,
                'codigo_postal': supplier.zip,
            }

            # Shipping.
            shipping = self.partner_shipping_id
            if shipping != customer:

                shipping_cfdi_values = dict(cfdi_values)
                # In case of COMEX we need to fill "NumRegIdTrib" with the real tax id of the customer
                # but let the generic RFC.
                self.env['l10n_mx_edi.document']._add_customer_cfdi_values(
                    shipping_cfdi_values,
                    customer=shipping,
                    usage=cfdi_values['receptor']['uso_cfdi'],
                    to_public=self.l10n_mx_edi_cfdi_to_public,
                )
                shipping_values = shipping_cfdi_values['receptor']
                if (
                    shipping.country_id == shipping.commercial_partner_id.country_id
                    and shipping_values['rfc'] == 'XEXX010101000'
                ):
                    shipping_vat = shipping.vat.strip() if shipping.vat else None
                else:
                    shipping_vat = None

                if shipping.country_id.l10n_mx_edi_code == 'MEX':
                    colony = shipping.l10n_mx_edi_colony_code
                    locality = shipping.l10n_mx_edi_locality_id.code
                    city = shipping.city_id.l10n_mx_edi_code
                else:
                    colony = shipping.l10n_mx_edi_colony
                    locality = shipping.l10n_mx_edi_locality
                    city = shipping.city

                if shipping.country_id.l10n_mx_edi_code in ('MEX', 'USA', 'CAN') or shipping.state_id.code:
                    state = shipping.state_id.code
                else:
                    state = 'NA'

                ext_trade_values['destinario'] = {
                    'num_reg_id_trib': shipping_vat,
                    'nombre': shipping.name,
                    'calle': shipping.street_name,
                    'numero_exterior': shipping.street_number,
                    'numero_interior': shipping.street_number2,
                    'colonia': colony,
                    'localidad': locality,
                    'municipio': city,
                    'estado': state,
                    'pais': shipping.country_id.l10n_mx_edi_code,
                    'codigo_postal': shipping.zip,
                }

            # Certificate.
            ext_trade_values['certificado_origen'] = '1' if self.l10n_mx_edi_cer_source else '0'
            ext_trade_values['num_certificado_origen'] = self.l10n_mx_edi_cer_source

            # Rate.
            mxn = self.env["res.currency"].search([('name', '=', 'MXN')], limit=1)
            usd = self.env["res.currency"].search([('name', '=', 'USD')], limit=1)
            ext_trade_values['tipo_cambio_usd'] = usd._get_conversion_rate(usd, mxn, self.company_id, self.date)
            if ext_trade_values['tipo_cambio_usd']:
                to_usd_rate = (cfdi_values['tipo_cambio'] or 1.0) / ext_trade_values['tipo_cambio_usd']
            else:
                to_usd_rate = 0.0

            # Misc.
            if customer.country_id and 'EU' in customer.country_id.country_group_codes:
                ext_trade_values['numero_exportador_confiable'] = self.company_id.l10n_mx_edi_num_exporter
            else:
                ext_trade_values['numero_exportador_confiable'] = None
            ext_trade_values['incoterm'] = self.invoice_incoterm_id.code
            ext_trade_values['observaciones'] = self.narration

            # Details per product.
            product_values_map = defaultdict(lambda: {
                'quantity_list': [],
                'price_unit_list': [],
                'total': 0.0,
            })
            for base_line in cfdi_values['base_lines']:
                product = base_line['product_id']
                product_values_map[product]['quantity_list'].append(base_line['l10n_mx_edi_qty_umt'])
                product_values_map[product]['price_unit_list'].append(base_line['l10n_mx_edi_price_unit_umt'])
                product_values_map[product]['total'] += base_line['l10n_mx_cfdi_values']['importe']
            ext_trade_values['total_usd'] = 0.0
            ext_trade_values['mercancia_list'] = []
            for product, product_values in product_values_map.items():
                total_usd = usd.round(product_values['total'] * to_usd_rate) if usd else 0.0
                weighted_prices = sum(price_unit * qty for (price_unit, qty) in zip(product_values['price_unit_list'], product_values['quantity_list']))
                weights = sum(product_values['quantity_list'])
                if weights != 0:
                    amount = weighted_prices / weights
                else:
                    amount = sum(product_values['price_unit_list']) / len(product_values['price_unit_list'])

                ############ Agregar inofrmación a los productos #############################
                series_len = 0
                desc_especifica = []

                for line_vals in self.invoice_line_ids:
                   if line_vals.product_id.id != product.id:
                        continue
                   if line_vals.info_mercancias:
                       if line_vals.info_mercancias.cce_series:
                           for serie in line_vals.info_mercancias.cce_series:
                               desc_especifica.append({
                                  'Marca': line_vals.info_mercancias.cce_marca,
                                  'Modelo': line_vals.info_mercancias.cce_modelo,
                                  'SubModelo': line_vals.info_mercancias.cce_submodelo,
                                  'NumeroSerie': serie.cce_numeroserie,
                               })
                           series_len =  len(line_vals.info_mercancias.cce_series)
                       else:
                           desc_especifica.append({
                                  'Marca': line_vals.info_mercancias.cce_marca,
                                  'Modelo': line_vals.info_mercancias.cce_modelo,
                                  'SubModelo': line_vals.info_mercancias.cce_submodelo,
                                  'NumeroSerie': None,
                           })
                ##########################################################

                ext_trade_values['mercancia_list'].append({
                    'no_identificacion': product.default_code,
                    'fraccion_arancelaria': product.l10n_mx_edi_tariff_fraction_id.code,
                    'cantidad_aduana': sum(product_values['quantity_list']),
                    'unidad_aduana': product.l10n_mx_edi_umt_aduana_id.l10n_mx_edi_code_aduana,
                    'valor_unitario_udana': float_round(amount * to_usd_rate, precision_digits=6),
                    'valor_dolares': total_usd,
                    'desc_especifica': desc_especifica,
                })
                ext_trade_values['total_usd'] += total_usd
        else:
            # Invoice lines.
            for base_line in cfdi_values['base_lines']:
                base_line_cfdi_values = base_line['l10n_mx_cfdi_values']
                base_line_cfdi_values['informacion_aduanera_list'] = base_line['l10n_mx_edi_custom_numbers']

