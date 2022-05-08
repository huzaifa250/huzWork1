
from odoo import models, fields, api, _


class Discount(models.Model):
    _name = "parent.discount.conf"

    date = fields.Date(required=True,default=fields.Date.today())
    name = fields.Char(required=True)
    line_ids = fields.One2many('discount.conf.line','discount_id')
    state = fields.Selection(selection=[('draft','Draft'),('confirm','Confirmed')],default='draft')

    def to_confirm(self):
    	self.state = 'confirm'

    	
class DiscountLines(models.Model):
    _name = "discount.conf.line"
    _rec_name = "discount"

    childs_no = fields.Integer()
    discount = fields.Float('Disc(%)')
    discount_id = fields.Many2one('parent.discount.conf')
    is_free = fields.Boolean(default=False)
    date = fields.Date(related='discount_id.date')
    state = fields.Selection(related='discount_id.state')