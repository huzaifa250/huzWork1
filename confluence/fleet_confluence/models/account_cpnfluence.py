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

class AccountMove(models.Model):
    _inherit = 'account.move'

    services_conflu_id = fields.Many2one("fleet.vehicle.log.services", string="Services")
    insurance_conflu_id = fields.Many2one("fleet.vehicle.log.services", string="Cars insurance")
    services_move_line_ids = fields.One2many("account.move.line", 'services_move_id', string="Services")
    vehicle_id_conflu_id = fields.Many2one("fleet.vehicle", string="Vehicle")
    is_services = fields.Boolean(string=" Is Services",default=False)
    is_insurance = fields.Boolean(string="Is Insurance",default=False)


class AccountMove(models.Model):
        _inherit = 'account.move.line'

        services_conflu_line_id = fields.Many2one("spare.parts.confluence", string="Spare parts")
        insurance_conflu_line_id = fields.Many2one("fleet.vehicle.log.services", string="Cars insurance")
        services_move_id = fields.Many2one("account.move", string="Services ACCOUNT ID")
        services_confluence_line_id = fields.Many2one("services.confluence", string="Cars insurance")
        name_services = fields.Char(string='Services')
        cost_services = fields.Float(string='cost')
        services_confluence = fields.Boolean(string='services')

