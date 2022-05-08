# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# import pytz
from datetime import datetime, time
# from dateutil.rrule import rrule, DAILY
# from random import choice
# from string import digits
# from werkzeug.urls import url_encode
from dateutil.relativedelta import relativedelta
# from collections import defaultdict

from odoo import api, fields, models, _
# from odoo.osv.query import Query
from odoo.exceptions import ValidationError, AccessError, UserError
# from odoo.osv import expression
# from odoo.tools.misc import format_date
# import date
import datetime

class StockPicking(models.Model):
    _inherit = "stock.picking"
    _description = "Stock confluence"

    op_level_id = fields.Many2one('op.level',string='Level')
    op_class_id = fields.Many2one('op.classroom',string='Class Room',domain="[('level_id','=',op_level_id)]")


