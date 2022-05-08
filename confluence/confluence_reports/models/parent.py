

from odoo import models, fields, api, _


class Parent(models.Model):
    _inherit = 'op.parent'

    year = fields.Char(default=lambda self : fields.Date.today().year)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)