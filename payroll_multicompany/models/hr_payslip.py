from odoo import models, fields, api


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True,
        default=lambda self: self.env['res.company']._company_default_get())
	
class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    parent_id = fields.Many2one('hr.payroll.structure', string='Parent', default=None)

    @api.model
    def _get_parent(self):
        return False
