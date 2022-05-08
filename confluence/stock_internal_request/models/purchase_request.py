# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare



class PUrchasetrequest(models.Model):
    _inherit = 'purchase.request'


    internal_request_id = fields.Many2one('internal.requisition', string='Internal Request Ref', copy=False)
    is_internal_request = fields.Boolean()

