# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MrpProductionPlanItem(models.TransientModel):
    _name = "mrp.production.plan.item"


    date = fields.Date('Fecha',default=fields.date.today(), readonly=True)
    sale_id = fields.Many2one('sale.order', string='Venta', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', readonly=True)
    code = fields.Char(related="product_id.default_code", string=u"Código", readonly=True)
    product_id = fields.Many2one('product.product', string=u'Descripción', readonly=True)
    qty_to_produce = fields.Float('SOL.', default=0, help="Cantidad a producir en la orden de manofactura", readonly=True)
    uom = fields.Many2one('uom.uom', string='UM', readonly=True)
    planned_date = fields.Datetime('Ing. Pedido',default=fields.datetime.now(), readonly=True)
    sale_date = fields.Date('Fecha',default=fields.date.today(), readonly=True)
    family = fields.Char(related="product_id.family",string='Familia', readonly=True)
    mrp_date = fields.Date('Fecha de fabricación',default=fields.date.today(), readonly=True)
    comp_date = fields.Datetime('Compromiso en planta')
    op_name = fields.Many2one('mrp.production', u'Órden de producción',readonly=True)
    pack = fields.Char('Pack')
    op_item_name = fields.Char(u'Órden de habilitado', readonly=True)
    code_item_name = fields.Many2one('product.product',u'Código de habilitado', readonly=True)
    qty = fields.Integer('Cantidad', default=0)
    dimension = fields.Char(u'Dimensión')
    incomming_date = fields.Date('Ingreso Físico', readonly=True)
    status = fields.Selection([    
            ('1',u'Pendiente OP/OH'),
            ('2',u'Surtir de inventario'),
            ('3',u'En espera de MP'),
            ('4',u'En espera de HAB'),
            ('5',u'Listo para producir'),
            ('6',u'Entregado a almacén'),
            ('7',u'Facturado/Entregado'),
            ('8',u'Detenido por ventas'),
            ('9',u'En espera de cierre'),
            ('10',u'Cancelado'),
            ('11',u'Detenido en Almacén '),
        ], string=u'Estatus producción')
    client_delivery_date = fields.Date('Fecha de entrega al cliente',default=fields.date.today(), readonly=True)
    invoice_id = fields.Many2one('account.move', string='N. Factura', readonly=True)
    delay = fields.Char('Retraso', readonly=True)
    delay_days = fields.Integer(u'Días entre ingreso y entrega', default=0, readonly=True)
    notes = fields.Text('Observaciones', readonly=True)
    completed = fields.Boolean('Completo', readonly=True)
    sale_time = fields.Integer(u'Tiempo que ventas deja para fabricar el producto', default=0, readonly=True)
    plant_time = fields.Integer(u'Tiempo que planta ofrecio para ese producto en la semana que entro el pedido', default=0, readonly=True)
    real_time = fields.Integer(u'Tiempo real en programa para entregar el producto', default=0, readonly=True, compute='_get_real_time')
    # Campos calculados
    is_delivery = fields.Boolean('Entregado',readonly=True)
    mrp_month = fields.Integer(u'Mes (Órden de producción)',readonly=True)
    sale_month = fields.Integer('Mes (Prom Vta)',readonly=True)
    sale_year = fields.Integer(u'Año (Prom Vta)',readonly=True)
    diff_days_delivery = fields.Integer(u'Entrega Almacén vs Fecha Promesa',readonly=True)
    retraso = fields.Char(u'Retraso Prod vs Almacén',readonly=False)
    production_finished = fields.Boolean(u'Producción', readonly=False)
    full_delivered = fields.Boolean('Entregado 100%')
    ###################
    weeknum = fields.Integer('Número de la semana (recepción - MRP)', default=0, readonly=True)
    year = fields.Integer('Año (recepción - MRP)', default=0, readonly=True)


    def _get_real_time(self):
        for line in self:
            line.real_time = 0
            if line.comp_date and line.incomming_date:
                num_days = (line.comp_date - line.incomming_date).days
                print("num_days: %s"%num_days)
                line.real_time = num_days if isinstance(num_days, int) else 0
            


    def create_records(self):
        print(u"Hola soy error")
        production_items = self
        # Crear registros transitorios basados en los registros de MRP y sale
        sale_line_ids = self.env['sale.order.line'].search([('state', 'not in', ['cancel','draft'])])
        print("sale_line_ids: %s"%sale_line_ids)
        for sale_line in sale_line_ids:
            # Si el producto tiene lista de materiales
            mrp_ids = self.env['mrp.production'].search([('product_id', '=', sale_line.product_id.id)])
            print("mrp_ids: %s"%mrp_ids)
            if sale_line.product_id.bom_ids:
                for mrp in mrp_ids:
                    invoice_ids = self.env['account.move']
                    print("(sale_line.order_id.effective_date - sale_line.order_id.commitment_date ): %s, %s"%(sale_line.order_id.effective_date, sale_line.order_id.commitment_date ))
                    if sale_line.order_id.invoice_ids:
                        invoice_ids = sale_line.order_id.invoice_ids.filtered(lambda x: x.state not in ['cancel','draft'])


                    def get_days(date1, date2):
                        if not date1 or not date2:
                            return 0
                        return (date1 - date2).days

                    values = {
                        'date': fields.date.today(),
                        'sale_id': sale_line.order_id.id,
                        'partner_id': sale_line.order_id.partner_id.id,
                        'code': sale_line.product_id.default_code,
                        'product_id': sale_line.product_id.id,
                        'qty_to_produce': sale_line.product_uom_qty,
                        'uom': sale_line.product_uom.id,
                        'planned_date': sale_line.order_id.date_order,
                        'sale_date': sale_line.order_id.expected_date,
                        'family': sale_line.product_id.family,
                        'mrp_date': mrp.date_planned_start,
                        'op_name': mrp.id,
                        'op_item_name': mrp.origin,
                        'code_item_name': mrp.product_id.id,
                        'qty': mrp.product_qty,
                        'dimension': mrp.product_id.description_pickingin,
                        'incomming_date': sale_line.order_id.x_studio_entrada_almacn,
                        'status': mrp.status,
                        'client_delivery_date': sale_line.order_id.confirmation_date,
                        'invoice_id': ', '.join(invoice_ids.mapped('display_name')) if invoice_ids else False,
                        'delay_days': get_days(sale_line.order_id.effective_date, sale_line.order_id.x_studio_entrada_almacn ),
                        'notes': sale_line.order_id.note,
                        'completed': sale_line.product_uom_qty == sale_line.qty_delivered,
                        'sale_time': get_days(sale_line.order_id.x_studio_entrada_almacn, sale_line.order_id.date_order ),
                        'plant_time': get_days(mrp.date_planned_start, sale_line.order_id.date_order ),
                        'real_time': get_days(sale_line.order_id.x_studio_fecha_compromiso_planta, sale_line.order_id.x_studio_entrada_almacn),
                        'is_delivery': sale_line.product_uom_qty == sale_line.qty_delivered,
                        'sale_month': sale_line.order_id.date_order.month if sale_line.order_id.date_order else False,
                        'sale_year': sale_line.order_id.date_order.year if sale_line.order_id.date_order else False,
                        'diff_days_delivery': get_days(sale_line.order_id.x_studio_entrada_almacn, sale_line.order_id.date_order ),
                        'retraso': get_days(sale_line.order_id.expected_date, sale_line.order_id.date_order) if  get_days(sale_line.order_id.expected_date, sale_line.order_id.date_order) < 1 else 'OT',
                        'production_finished': mrp.state == 'done',
                        'full_delivered':  sale_line.product_uom_qty == sale_line.qty_delivered and mrp.state == 'done',
                        'mrp_month': mrp.date_start.month if mrp.date_start else False,
                        'weeknum':int(mrp.date_finished.strftime("%V")),
                        'year': mrp.date_finished.year,
                        'comp_date': sale_line.order_id.x_studio_fecha_compromiso_planta,
                    }
        
                    production_items += self.create(values)

        action = {
            'name': u'Plan de producción',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'mrp.production.plan.item',
            'domain': [('id', 'in', production_items.ids)],
        }
        print("action: %s"%action)
        return action

