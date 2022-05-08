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
# Subset of partner fields: sync all or none to avoid mixed addresses
PARTNER_ADDRESS_FIELDS_TO_SYNC = [
    'street',
    'street2',
    'city',
    'zip',
    'state_id',
    'country_id',
]


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = " HR Employee confluence"

    staff_type = fields.Selection([('local_staff', 'Local Staff'),('international_staff', 'International staff')], string='Type of Staff', required=True)
    sequence = fields.Char(string='Sequence',readonly=True,rack_visibility='onchange', index=True, default=lambda self: _( 'NEW' ))
    age = fields.Char(string='Age',compute='compute_employee_age')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', check_company=True, index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")

    # Address fields
    street = fields.Char('Street', compute='_compute_partner_address_values', readonly=False, store=True)
    street2 = fields.Char('Street2', compute='_compute_partner_address_values', readonly=False, store=True)
    zip = fields.Char('Zip', change_default=True, compute='_compute_partner_address_values', readonly=False, store=True)
    city = fields.Char('City', compute='_compute_partner_address_values', readonly=False, store=True)
    state_id = fields.Many2one(
        "res.country.state", string='State',
        compute='_compute_partner_address_values', readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(
        'res.country', string='Country',
        compute='_compute_partner_address_values', readonly=False, store=True)
    # current Address fields
    street_current = fields.Char('Street', compute='_compute_partner_address_values', readonly=False, store=True)
    street2_current = fields.Char('Street2', compute='_compute_partner_address_values', readonly=False, store=True)
    zip_current = fields.Char('Zip', change_default=True, compute='_compute_partner_address_values', readonly=False, store=True)
    city_current = fields.Char('City', compute='_compute_partner_address_values', readonly=False, store=True)
    state_id_current = fields.Many2one(
        "res.country.state", string='State',
        compute='_compute_partner_address_values', readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")
    country_id_current = fields.Many2one(
        'res.country', string='Country',
        compute='_compute_partner_address_values', readonly=False, store=True)

    @api.depends('partner_id')
    def _compute_partner_address_values(self):
        """ Sync all or none of address fields """
        for lead in self:
            lead.update(lead._prepare_address_values_from_partner(lead.partner_id))

    def _prepare_address_values_from_partner(self, partner):
        # Sync all address fields from partner, or none, to avoid mixing them.
        if any(partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC):
            values = {f: partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
        else:
            values = {f: self[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
        return values

    @api.model
    def create(self, vals):
        result = super(HrEmployee, self).create(vals)
        # month = datetime.strptime(result.date(field), '%Y-%m-%d').strftime('%m')
        if vals.get('sequence', 'New') == 'New':
            result.name = self.env['ir.sequence'].next_by_code(
                'hr.employee') or 'New'

        return result
    def  compute_employee_age(self):
        for rec in self:
            today = fields.Date.today()
            rec.age = 0
            if rec.birthday:
                rec.age = today.year - rec.birthday.year - ((today.month, today.day) < (rec.birthday.month, rec.birthday.day))

