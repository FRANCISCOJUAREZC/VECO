# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, datetime

class MrpProductionPlanItem(models.Model):
    _name = "mrp.production.plan.item"

    #Campos no mostrados pero utiles
    sale_line_id = fields.Many2one('sale.order.line', string='Linea de venta')
    # Campos de venta
    in_date = fields.Date('Ingreso',default=fields.date.today())
    sale_id = fields.Many2one(related="sale_line_id.order_id", string='Venta')
    partner_id = fields.Many2one(related="sale_line_id.order_id.partner_id", string="Cliente")
    product_id = fields.Many2one(related="sale_line_id.product_id", string=u'Descripción')
    qty_to_produce = fields.Float(related="sale_line_id.product_uom_qty",string='SOL.', help="Cantidad a producir en la orden de manofactura")
    uom = fields.Many2one(related="sale_line_id.product_uom", string='UM')
    planned_date = fields.Datetime(related="sale_id.date_order", string=u"Fecha aprobación")
    sale_date = fields.Datetime(related="sale_id.commitment_date",string='Fecha promesa de ventas')
    family = fields.Char(related="product_id.family",string='Familia')
    # Campos MRP
    mrp_date = fields.Datetime(related="mrp_id.x_studio_fecha_inicio_fabrticacion",string='Fecha de fabricación')
    comp_date = fields.Datetime(related="sale_id.x_studio_fecha_compromiso_planta",string='Compromiso en planta',readonly=False)
    mrp_id = fields.Many2one('mrp.production', string=u'Órden de producción')
    pack = fields.Char('Pack')
    # Habilitado
    hability_mrp_id = fields.Many2one('mrp.production',string=u'Órden de habilitado')
    hability_product_id = fields.Many2one(related="hability_mrp_id.product_id",string=u'Código de habilitado')
    hability_qty = fields.Float(related="hability_mrp_id.product_qty", default=0)
    hability_dimension = fields.Text(related="hability_mrp_id.product_id.description_pickingin")
    hability_incomming_date = fields.Datetime(u'Ingreso Físico al almacén')
    # MRP 
    status = fields.Selection(related="mrp_id.x_studio_estatus_de_produccin",string=u'Estatus producción', readonly=False)
    client_delivery_date = fields.Datetime('Fecha de entrega al cliente')
    invoice_list = fields.Char(string='N. Factura')
    #
    delay = fields.Char('Retraso')
    notes = fields.Text(related="sale_id.note",string='Observaciones', readonly=False)
    completed = fields.Boolean('Completo')
    # Campos calculados (fechas)
    delay_days = fields.Integer(u'Días entre ingreso y entrega', default=0, compute="_compute_dates")
    sale_time = fields.Integer(u'Tiempo que ventas deja para fabricar el producto', default=0,compute="_compute_dates")
    plant_time = fields.Integer(u'Tiempo que planta ofrecio para ese producto en la semana que entro el pedido', default=0,compute="_compute_dates")

    sale_week = fields.Char('Semana (Prom Vta)', compute="_compute_dates")
    sale_month = fields.Char('Mes (Prom Vta)', compute="_compute_dates")
    sale_year = fields.Char(u'Año (Prom Vta)', compute="_compute_dates")
    weeknum = fields.Char('Número de la semana (recepción - MRP)', default=0, compute="_compute_dates")
    mrp_month = fields.Char(u'Mes (Órden de producción)',compute="_compute_dates")
    year = fields.Char('Año (recepción - MRP)', default=0,compute="_compute_dates")
    # Campos calculados (char)
    prod_delay_warehouse = fields.Char(u'Retraso Prod vs Almacén',readonly=False, compute='_get_prod_delay')
    production= fields.Boolean(u'Producción',compute='_get_prod_delay')
    is_delivery = fields.Boolean('Entregado',compute='_get_prod_delay')
    #
    diff_days_delivery = fields.Integer(u'Entrega Almacén vs Fecha Promesa')
    full_delivered = fields.Boolean('Entregado 100%')
    ###################

    def _get_delivery_client_delay(self):
        for item in self:
            # 'Entrega Almacén vs Fecha Promesa
            # Si fecha entrega cliente es mayor a la fecha promeda de ventas
            # ingreso fisico - fecha promesa 
            # si el ingreso fisico esta vacio PEND
            promise_date = item.sale_date
            value = 'OT'
            if not item.client_delivery_date or not promise_date:
                value = 'PEND'
            elif item.client_delivery_date > promise_date:
                value = str(item.get_diff_dates(item.client_delivery_date, item.sale_date))
            
            item.full_delivery = value == 'OT'
            item.diff_days_delivery = value


    def _get_prod_delay(self):
        for item in self:
            # Retraso Prod vs Almacén
            # Si ingreso fisico al almacen es mayor a la fecha promeda de ventas
            # ingreso fisico - fecha promesa 
            # si el ingreso fisico esta vacio PEND
            promise_date = item.sale_date
            value = 'OT'
            if not item.hability_incomming_date or not promise_date:
                value = 'PEND'
            elif item.hability_incomming_date > promise_date:
                value = str(item.get_diff_dates(item.hability_incomming_date, item.sale_date))
            
            item.production = value == 'OT'
            item.prod_delay_warehouse = value
            item.is_delivery = item.status == "c. Facturado/Entregado"

    def _compute_dates(self):
        now = fields.datetime.now()
        for item in self:
            # dias ingreso y entrega
            item.delay_days = item.get_diff_dates(item.client_delivery_date, item.in_date)
            # fecha promesa de entrega - ingreso pedido (aprobacion)
            item.sale_time = item.get_diff_dates(item.sale_date, item.planned_date)
            # fecha compromiso planta - ingreso pedido (aprobacion)
            item.plant_time = item.get_diff_dates(item.comp_date, item.planned_date)
            # Numero de semana de promesa de venta
            item.sale_week = str(item.sale_date.strftime("%V")) if item.sale_date else False
            # Mes de promesa de venta
            item.sale_month = str(item.sale_date.month) if item.sale_date else False
            # año de promesa de venta
            item.sale_year = str(item.sale_date.year) if item.sale_date else False
            # Entrega  (ingreso fisico al almacen) vs Fecha Promesa Cliente
            item.sale_time = item.get_diff_dates(item.hability_incomming_date, item.sale_date)
            # Numero de semana de fecha de fabricacion
            item.weeknum = str(item.mrp_date.strftime("%V")) if item.mrp_date else False
            # Mes fecha fabricacion
            item.mrp_month = str(item.mrp_date.month) if item.mrp_date else False
            # Año fecha fabricacion
            item.year = str(item.mrp_date.year) if item.mrp_date else False

            
    def get_diff_dates(self,date1, date2):
        if isinstance(date1, date):
            date1 = datetime.combine(date.today(), datetime.min.time())

        if isinstance(date2, date):
            date2 = datetime.combine(date.today(), datetime.min.time())

        if not date1 or not date2:
            return 0
        return (date1 - date2).days

    def create_records(self):
        production_items = self
        current_rows = self.search([])
        # Crear registros transitorios basados en los registros de MRP y sale
        search_values = [\
            ('state', 'not in', ['cancel','draft']),\
            ]
        if current_rows and current_rows.mapped('sale_line_id'):
            search_values.append(('id','not in',current_rows.mapped('sale_line_id.id')))

        sale_line_ids = self.env['sale.order.line'].search(search_values)
        

        mrp_production_order_ids = self.env['mrp.production'].search([('state', '!=', 'cancel'),('id','not in',current_rows.mapped('mrp_id.id'))])

        for mrp in mrp_production_order_ids:
            # MRP values
            sale_line_ids = mrp.x_studio_sale_id.order_line.filtered(lambda x: x.product_id == mrp.product_id)
            sale_line = sale_line_ids[0] if sale_line_ids else self.env['sale.order.line']
            sale_picking = sale_line.order_id.picking_ids.filtered(lambda x: x.state == 'done')
            sale_picking_date_done = False

            invoice_ids = sale_line.order_id.invoice_ids.filtered(lambda x: x.state not in ['draft','cancel'])
            if sale_picking:
                sale_picking_date_done = sale_picking[0].date_done
  
            if mrp:
                hability_mrp_ids = self.env['mrp.production'].search([('origin', '=', mrp.name)])
                if hability_mrp_ids:
                    for hability_mrp_id in hability_mrp_ids:
                        # Obtencion de los campos de la orden de hablitado
                        dest_location = hability_mrp_id.location_dest_id or self.env['stock.location']
                        hability_sfp_picking = hability_mrp_id.picking_ids.filtered(lambda x: x.location_id == dest_location)
                        hability_incomming_date = False
                        if hability_sfp_picking:
                            hability_incomming_date = hability_sfp_picking[0].date_done or False

                        if hability_mrp_id:
                            values = {
                                'sale_line_id':sale_line.id,
                                'mrp_id':mrp.id,
                                'hability_mrp_id': hability_mrp_id.id if hability_mrp_id else False,
                                'hability_incomming_date': hability_incomming_date,
                                'client_delivery_date': sale_picking_date_done,
                                'invoice_list': ', '.join(invoice_ids.mapped('display_name')) if invoice_ids else False,
                            }
                            production_items += self.create(values)
                else:
                    values = {
                        'sale_line_id':sale_line.id,
                        'mrp_id':mrp.id,
                        'client_delivery_date': sale_picking_date_done,
                        'invoice_list': ', '.join(invoice_ids.mapped('display_name')) if invoice_ids else False,
                    }
                    production_items += self.create(values)


            production_items += self.create(values)

        action = {
            'name': u'Plan de producción',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production.plan.item',
            'domain': [('id', 'in', production_items.ids)],
        }
        return action

