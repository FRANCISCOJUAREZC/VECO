# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError



class ProductionPlanWizard(models.TransientModel):
    _name = "production.plan.wizard"
    
    def action_generate(self):
        prod_plan = self.env['mrp.production.plan.item']
        return prod_plan.create_records()