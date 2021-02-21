# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
#from tzlocal import get_localzone
from datetime import datetime
from odoo.exceptions import UserError


class RetardoNomina(models.Model):
    _name = 'retardo.nomina'
    _description = 'RetardoNomina'

    name = fields.Char("Name", required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    fecha = fields.Date('Fecha')
    state = fields.Selection([('draft', 'Borrador'), ('done', 'Hecho'), ('cancel', 'Cancelado')], string='State', default='draft')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    @api.model
    def init(self):
        company_id = self.env['res.company'].search([])
        for company in company_id:
            retardo_nomina_sequence = self.env['ir.sequence'].search([('code', '=', 'retardo.nomina'), ('company_id', '=', company.id)])
            if not retardo_nomina_sequence:
                retardo_nomina_sequence.create({
                        'name': 'Retardo nomina',
                        'code': 'retardo.nomina',
                        'padding': 4,
                        'company_id': company.id,
                    })

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('retardo.nomina') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('retardo.nomina') or _('New')
        result = super(RetardoNomina, self).create(vals)
        return result

    @api.multi
    def action_validar(self):
        self.write({'state':'done'})
        return

    @api.multi
    def action_cancelar(self):
        self.write({'state':'cancel'})

    @api.multi
    def action_draft(self):
        self.write({'state':'draft'})

    @api.multi
    def unlink(self):
        raise UserError("Los registros no se pueden borrar, solo cancelar.")

    def action_change_state(self):
        for retardo in self:
            if retardo.state == 'draft':
                retardo.action_validar()
