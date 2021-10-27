# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    family = fields.Char('Familia')


class MrpProduction(models.Model):
    _inherit = "mrp.production"


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
    
    