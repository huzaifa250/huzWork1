# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# import pytz
from datetime import datetime, time
# from dateutil.rrule import rrule, DAILY
# from random import choice
# from string import digits
# from werkzeug.urls import url_encode
# from dateutil.relativedelta import relativedelta
# from collections import defaultdict

from odoo import api, fields, models, _
# from odoo.osv.query import Query
from odoo.exceptions import ValidationError, AccessError, UserError
# from odoo.osv import expression
# from odoo.tools.misc import format_date
# import date
import datetime

class SparePartsConfluence(models.Model):
    _name = "spare.parts.confluence"
    _description = " Spare Parts confluence"

    product_id = fields.Many2one('product.product', 'Spare')
    name= fields.Char(string='Description')
    quantity_spare= fields.Integer(string='Quantity')
    cost_spare= fields.Float(string='cost')
    cost_total= fields.Float(string='Total cost',compute='compute_total_cost')
    fleet_services_id = fields.Many2one('fleet.vehicle.log.services', string='Fleet Services')


    @api.depends('quantity_spare','cost_spare')
    def compute_total_cost(self):
        for rec in self:
            rec.cost_total =rec.quantity_spare * rec.cost_spare


    @api.onchange('product_id')
    def _onchange_cost_spare(self):
        if self.product_id:
            self.cost_spare = self.product_id.list_price


class ServicesConfluence(models.Model):
    _name = "services.confluence"
    _description = "Services confluence"

    product_id = fields.Many2one('product.product', 'Services',domain = lambda self: self.action_domain())
    name = fields.Char(string='Description')
    cost_services = fields.Float(string='cost')

    fleet_services_confluence_id = fields.Many2one('fleet.vehicle.log.services', string='Fleet Services')

    def action_domain(self):
        return [
            ('sale_ok', '=', True)]and [('type', '=', 'service')]
    # @api.depends('quantity_spare','cost_spare')
    # def compute_total_cost(self):
    #     for rec in self:
    #         rec.cost_total =rec.quantity_spare * rec.cost_spare