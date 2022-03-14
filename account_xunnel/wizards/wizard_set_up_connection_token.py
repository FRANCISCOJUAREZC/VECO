from odoo import fields, models


class WizardNewtoken(models.TransientModel):
    _name = 'wizard.set.up.connection.token'
    _description = """Wizard to set the Xunnel Token of your company, this is given when you
    create a company at https://www.xunnel.com/"""

    xunnel_token = fields.Char(default=lambda self: self.env.company.xunnel_token, readonly=False)

    def confirm(self):
        self.env.company.sudo().xunnel_token = self.xunnel_token
