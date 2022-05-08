# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError, UserError
import datetime

class HrContract(models.Model):
	_inherit = "hr.contract"
	_description = " HR Contract confluence"

	staff_type = fields.Selection(related='employee_id.staff_type',string='Staff Type',store=True)
	date_end = fields.Date('End Date', tracking=True, compute='compute_date_end',
						   help="End date of the contract (if it's a fixed-term contract).")
	allowances= fields.Float(compute='compute_salary_details',string='Allowances',store=True)
	salary= fields.Float(compute='compute_salary_details',string='Salary',store=True)
	basic= fields.Float(string='Basic')
	cola= fields.Float(string='Cola')
	subsistence= fields.Float(string='Subsistence')
	clothing= fields.Float(string='Clothing')
	transportation= fields.Float(string='Transportation')
	transportation_international= fields.Float(string='Transportation INT')
	transportation_fixed= fields.Float(string='Transportation Fixed')
	visa_expenses= fields.Float(string='Visa expenses')
	tickets= fields.Float(string='Tickets')
	medical_insurance= fields.Float(string='Medical Insurance')
	wage = fields.Monetary('Wage', required=True, tracking=True, currency_field='currency',help="Employee's monthly gross wage.")
	currency = fields.Many2one('res.currency', string='Contract Currency', compute="_get_currency")


	@api.depends('staff_type')
	def _get_currency(self):
		for rec in self:
			if rec.staff_type == 'local_staff':
				rec.currency = self.env['res.currency'].search([('symbol','=','ج.س.')],limit=1)
			else:
				rec.currency = self.env['res.currency'].search([('symbol','=','$')],limit=1)
				
	def compute_date_end(self):
		for rec in self:
			rec.date_end = fields.Date.today()
			if rec.staff_type == 'local_staff':
				rec.date_end = rec.date_start + relativedelta(years=1)
			else:
				rec.date_end = rec.date_start + relativedelta(years=2)

	def compute_salary_details(self):
		for rec in self:
			wage = rec.wage
			rec.allowances =0.0
			rec.salary =0.0
			if rec.wage:
				rec.allowances = wage * 0.6
				rec.salary = wage * 0.4
				if rec.salary:
					rec.basic = rec.salary * 0.6
					rec.cola = rec.salary * 0.2
					rec.subsistence = rec.salary * 0.1
					rec.clothing = rec.salary * 0.05
					rec.transportation = rec.salary * 0.05




