# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenEduCat Inc
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<http://www.openeducat.org>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class OpAdmission(models.Model):
	_name = "op.admission"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_rec_name = "application_number"
	_description = "Admission"
	_order = 'id DESC'

	name = fields.Char(
		'Name', size=128, required=True, translate=True,copy=False)
	first_name = fields.Char(
		'First Name', size=128, required=True, translate=True,copy=False)
	middle_name = fields.Char(
		'Middle Name', size=128, required=True,translate=True,
		states={'done': [('readonly', True)]},copy=False)
	last_name = fields.Char(
		'Last Name', size=128, required=True, translate=True,
		states={'done': [('readonly', True)]},copy=False)
	forth_name = fields.Char(
		'Forth Name', size=128, required=True, translate=True,
		states={'done': [('readonly', True)]},copy=False)
	title = fields.Many2one(
		'res.partner.title', 'Title', states={'done': [('readonly', True)]})
	application_number = fields.Char(
		'Application Number', size=16, copy=False,
		required=True, readonly=True, store=True,
		default=lambda self:
		self.env['ir.sequence'].next_by_code('op.admission'))
	admission_date = fields.Date(
		'Admission Date', copy=False,
		states={'done': [('readonly', True)]},
		default=lambda self: fields.Datetime.now())
	application_date = fields.Datetime(
		'Application Date', required=True, copy=False,
		states={'done': [('readonly', True)]},
		default=lambda self: fields.Datetime.now())
	birth_date = fields.Date(
		'Birth Date', required=True, states={'done': [('readonly', True)]},copy=False)
	level_id = fields.Many2one(
		'op.level', 'Grade', required=True,
		states={'done': [('readonly', True)]})
	batch_id = fields.Many2one(
		'op.batch', 'Batch', required=False,
		states={'done': [('readonly', True)],
				'submit': [('required', True)],
				'fees_paid': [('required', True)]})
	street = fields.Char(
		'Street', size=256, states={'done': [('readonly', True)]})
	street2 = fields.Char(
		'Street2', size=256, states={'done': [('readonly', True)]})
	phone = fields.Char(
		'Phone', size=16, states={'done': [('readonly', True)],
								  'submit': [('required', True)]})
	mobile = fields.Char(
		'Mobile', size=16,
		states={'done': [('readonly', True)], 'submit': [('required', True)]})
	email = fields.Char(
		'Email', size=256, required=True,
		states={'done': [('readonly', True)]})
	city = fields.Char('City', size=64, states={'done': [('readonly', True)]})
	zip = fields.Char('Zip', size=8, states={'done': [('readonly', True)]})
	state_id = fields.Many2one(
		'res.country.state', 'States', states={'done': [('readonly', True)]})
	country_id = fields.Many2one(
		'res.country', 'Country', states={'done': [('readonly', True)]})
	# fees = fields.Float('Fees', states={'done': [('readonly', True)]})
	image = fields.Image('image', states={'done': [('readonly', True)]})
	state = fields.Selection(
		[('draft', 'Draft'), ('submit', 'Submitted'),
		 ('confirm', 'Assessment'), ('admission', 'Under Registration'),
		 ('reject', 'Rejected'), ('pending', 'Pending'),
		 ('cancel', 'Cancelled'), ('registration', 'Registration Done'),
		 ('done', 'Done')],
		'State', default='draft', tracking=True)
	due_date = fields.Date('Due Date', states={'done': [('readonly', True)]})
	prev_institute_id = fields.Char('Previous Institute',
									states={'done': [('readonly', True)]})
	prev_level_id = fields.Char('Previous Grade',
								 states={'done': [('readonly', True)]})
	prev_result = fields.Char(
		'Previous Result', size=256, states={'done': [('readonly', True)]})
	family_business = fields.Char(
		'Family Business', size=256, states={'done': [('readonly', True)]})
	family_income = fields.Float(
		'Family Income', states={'done': [('readonly', True)]})
	gender = fields.Selection(
		[('m', 'Male'), ('f', 'Female'), ('o', 'Other')],
		string='Gender',
		required=True,
		states={'done': [('readonly', True)]},copy=False)
	student_id = fields.Many2one(
		'op.student', 'Student', states={'done': [('readonly', True)]})
	nbr = fields.Integer('No of Admission', readonly=True)
	register_id = fields.Many2one(
		'op.admission.register', 'Admission Register', required=True,
		states={'done': [('readonly', True)]})
	partner_id = fields.Many2one('res.partner', 'Partner')
	is_student = fields.Boolean('Is Already Student')
	active = fields.Boolean(default=True)
	# discount = fields.Float(string='Discount (%)',
	#                         digits='Discount', default=0.0)

	fees_start_date = fields.Date('Fees Start Date')
	company_id = fields.Many2one(
		'res.company', string='Company',
		default=lambda self: self.env.user.company_id)

	father_name = fields.Char(
		'Name', size=256, states={'done': [('readonly', True)]})
	father_citizenship = fields.Char(
		'Citizenship', size=256, states={'done': [('readonly', True)]})
	father_occupation = fields.Char(
		'Occupation', size=256, states={'done': [('readonly', True)]})
	father_occupation_tit = fields.Char(
		'Title', size=256, states={'done': [('readonly', True)]})
	father_telephone = fields.Char(
		'Work Telephone', size=256, states={'done': [('readonly', True)]})
	father_mobile = fields.Char(
		'Mobile', size=256, states={'done': [('readonly', True)]})
	father_email = fields.Char(
		'Email', size=256, states={'done': [('readonly', True)]})
	father_birth_place = fields.Char(
		'Plase of Birth', size=256, states={'done': [('readonly', True)]})
	father_company = fields.Char(
		'Company/Business', size=256, states={'done': [('readonly', True)]})

	mother_name = fields.Char(
		'Name', size=256, states={'done': [('readonly', True)]})
	mother_citizenship = fields.Char(
		'Citizenship', size=256, states={'done': [('readonly', True)]})
	mother_occupation = fields.Char(
		'Occupation', size=256, states={'done': [('readonly', True)]})
	mother_occupation_tit = fields.Char(
		'Title', size=256, states={'done': [('readonly', True)]})
	mother_telephone = fields.Char(
		'Work Telephone', size=256, states={'done': [('readonly', True)]})
	mother_mobile = fields.Char(
		'Mobile', size=256, states={'done': [('readonly', True)]})
	mother_email = fields.Char(
		'Email', size=256, states={'done': [('readonly', True)]})
	mother_birth_place = fields.Char(
		'Plase of Birth', size=256, states={'done': [('readonly', True)]})
	mother_company = fields.Char(
		'Company/Business', size=256, states={'done': [('readonly', True)]})

	silbing_1 = fields.Char(
		 size=128, states={'done': [('readonly', True)]})
	silbing_1_age = fields.Char(
		'Age', size=128, states={'done': [('readonly', True)]})
	silbing_2 = fields.Char(
		 size=128, states={'done': [('readonly', True)]})
	silbing_2_age = fields.Char(
		'Age', size=128, states={'done': [('readonly', True)]})
	silbing_3 = fields.Char(
		 size=128, states={'done': [('readonly', True)]})
	silbing_3_age = fields.Char(
		'Age', size=128, states={'done': [('readonly', True)]})
	silbing_4 = fields.Char(
		 size=128, states={'done': [('readonly', True)]})
	silbing_4_age = fields.Char(
		'Age', size=128, states={'done': [('readonly', True)]})

	language = fields.Many2one('res.lang')

	medical_certificate = fields.Binary(string="Medical Certificate", )
	passport = fields.Binary(string="Passport",copy=False )
	vaccination_card = fields.Binary(string="Vaccination Card",copy=False )
	assessment_ids = fields.One2many('assessment.result','admission_id',copy=False)
	is_transfered = fields.Boolean('Come Form Another School ?')

	std_citizenship_1 = fields.Char(
		'Citizenship 1', size=256)
	std_citizenship_2 = fields.Char(
		'Citizenship 2', size=256)
	place_of_birth = fields.Char( size=256,copy=False)
	area = fields.Char(size=128)
	prev_result_ids = fields.One2many('previous.school.result','admission_id')
	student_custody = fields.Selection(selection=[('joint','Joint'),('father','Father'),
		('mother','Mother'),('other','Other')],default='joint')
	other_custody = fields.Char()
	parent_id = fields.Many2one('op.parent',required=True,string="Student Parent")
	student_sibing_no = fields.Integer(compute='get_student_sibing_no',store=True,copy=False)
	discount = fields.Float(compute='get_discount',store=True)
	actual_fees = fields.Float('Fees After Discount',compute="_get_actual_fees",store=True)
	study_fees = fields.Float(related='level_id.study_fees')
	registration_fees = fields.Float(related='level_id.registration_fees')
	class_id = fields.Many2one('op.classroom')
	invoice_id1 = fields.Many2one('account.move', 'Study Fees Invoice')
	invoice_id2 = fields.Many2one('account.move', 'Registration Fees Invoice')
	fees_detail_ids = fields.One2many('op.student.fees.details',
									  'admission_id',
									  string='Fees Collection Details',
									  )
	academic_years_id = fields.Many2one('op.academic.year',
						'Academic Year', readonly=True,
						states={'draft': [('readonly', False)]},
						tracking=True)
	academic_term_id = fields.Many2one('op.academic.term',
									   'Academic Terms', readonly=True,
									   states={'draft': [('readonly', False)]},
									   tracking=True)
	_sql_constraints = [
		('unique_application_number',
		 'unique(application_number)',
		 'Application Number must be unique per Application!'),
	]

	@api.onchange('first_name', 'middle_name', 'last_name','forth_name')
	def _onchange_name(self):
		self.name = str(self.first_name) + " " + str(
			self.middle_name) + " " + str(self.last_name) + " " + str(self.forth_name)

	@api.onchange('student_id', 'is_student')
	def onchange_student(self):
		if self.is_student and self.student_id:
			sd = self.student_id
			self.title = sd.title and sd.title.id or False
			self.first_name = sd.first_name
			self.middle_name = sd.middle_name
			self.last_name = sd.last_name
			self.forth_name = sd.forth_name
			self.birth_date = sd.birth_date
			self.gender = sd.gender
			self.image = sd.image_1920 or False
			self.street = sd.street or False
			self.street2 = sd.street2 or False
			self.phone = sd.phone or False
			self.mobile = sd.mobile or False
			self.email = sd.email or False
			self.zip = sd.zip or False
			self.city = sd.city or False
			self.country_id = sd.country_id and sd.country_id.id or False
			self.state_id = sd.state_id and sd.state_id.id or False
			self.partner_id = sd.partner_id and sd.partner_id.id or False
		else:
			self.birth_date = ''
			self.gender = ''
			self.image = False
			self.street = ''
			self.street2 = ''
			self.phone = ''
			self.mobile = ''
			self.zip = ''
			self.city = ''
			self.country_id = False
			self.state_id = False
			self.partner_id = False

	@api.onchange('register_id')
	def onchange_register(self):
		self.level_id = self.register_id.level_id
		self.study_fees = self.level_id.study_fees
		self.registration_fees = self.level_id.registration_fees
		self.company_id = self.register_id.company_id
		self.academic_years_id = self.register_id.academic_years_id
		self.academic_term_id = self.register_id.academic_term_id

	@api.onchange('level_id')
	def onchange_level(self):
		self.batch_id = False
		if self.level_id and self.level_id.study_fees:
			self.study_fees = self.level_id.study_fees
		if self.level_id and self.level_id.registration_fees:
			self.registration_fees = self.level_id.registration_fees

	@api.constrains('register_id', 'application_date')
	def _check_admission_register(self):
		for rec in self:
			start_date = fields.Date.from_string(rec.register_id.start_date)
			end_date = fields.Date.from_string(rec.register_id.end_date)
			application_date = fields.Date.from_string(rec.application_date)
			if application_date < start_date or application_date > end_date:
				raise ValidationError(_(
					"Application Date should be between Start Date & \
					End Date of Admission Register."))

	@api.constrains('birth_date')
	def _check_birthdate(self):
		for record in self:
			if record.birth_date > fields.Date.today():
				raise ValidationError(_(
					"Birth Date can't be greater than current date!"))
			elif record:
				today_date = fields.Date.today()
				day = (today_date - record.birth_date).days
				years = day // 365
				if years < self.register_id.minimum_age_criteria:
					raise ValidationError(_(
						"Not Eligible for Admission minimum required age is : %s " % self.register_id.minimum_age_criteria))


	@api.depends('student_sibing_no')
	def get_discount(self):
		for rec in self:
			discount = 0
			discount_ids = self.env['parent.discount.conf'].search([
				('date','>=',rec.register_id.start_date),
				('date','<=',rec.register_id.end_date),
				('state','=','confirm')
			])
			if discount_ids:
				discount_id = self.env['parent.discount.conf'].browse(max(discount_ids.ids))
				for line in discount_id.mapped('line_ids'):
					if line.childs_no == rec.student_sibing_no + 1:
						if line.is_free:
							discount = 100
						else:
							discount = line.discount
			else:
				if rec.student_sibing_no + 1 == 2:
					discount = 10
				if rec.student_sibing_no + 1 == 3:
					discount = 15
				if rec.student_sibing_no + 1 == 4:
					discount = 20
				if rec.student_sibing_no + 1 >= 5:
					discount = 100

			rec.discount = discount

	@api.depends('parent_id')
	def get_student_sibing_no(self):
		for rec in self:
			if rec.parent_id:
				rec.student_sibing_no = self.env['op.student'].search_count([('parent_id','=',rec.parent_id.id)])
			else:
				rec.student_sibing_no = 0

	@api.depends('study_fees','discount')
	def _get_actual_fees(self):
		for rec in self:
			if rec.discount != 0.0:
				rec.actual_fees = rec.study_fees - ( (rec.study_fees * rec.discount)/100 )
			else:
				rec.actual_fees = rec.study_fees

	def submit_form(self):
		self.state = 'submit'

	def admission_confirm(self):
		if not self.assessment_ids:
			ValidationError(_('You must enter assessment result firstly !!'))
		self.state = 'admission'

	def confirm_in_progress(self):
		for record in self:
			record.state = 'confirm'

	def get_student_vals(self):
		for student in self:
			student_user = self.env['res.users'].create({
				'name': student.name,
				'login': student.email,
				'image_1920': self.image or False,
				'is_student': True,
				'company_id': self.company_id.id,
				'groups_id': [
					(6, 0,
					 [self.env.ref('base.group_portal').id])]
			})
			details = {
				'phone': student.phone,
				'mobile': student.mobile,
				'email': student.email,
				'street': student.street,
				'street2': student.street2,
				'city': student.city,
				'country_id':
					student.country_id and student.country_id.id or False,
				'state_id': student.state_id and student.state_id.id or False,
				'image_1920': student.image,
				'zip': student.zip,
			}
			student_user.partner_id.write(details)
			details.update({
				'title': student.title and student.title.id or False,
				'first_name': student.first_name,
				'middle_name': student.middle_name,
				'last_name': student.last_name,
				'forth_name': student.forth_name,
				'birth_date': student.birth_date,
				'parent_id': student.parent_id.id,
				'gender': student.gender,
				'image_1920': student.image or False,
				'academic_years_id': student.register_id.academic_years_id.id,
				'academic_term_id': student.register_id.academic_term_id.id,
				'level_detail_ids': [[0, False, {
					'level_id':
						student.level_id and student.level_id.id or False,
					'class_id':
						student.class_id and student.class_id.id or False,
					'batch_id':
						student.batch_id and student.batch_id.id or False,
					'academic_years_id': student.register_id.academic_years_id.id or False,
					'academic_term_id': student.register_id.academic_term_id.id or False,
					'subject_ids': [(6, 0, student.level_id.subject_ids.ids)],
					'registration_fees': student.level_id.registration_fees or False,
					'study_fees': student.level_id.study_fees or False,
					'discount': student.discount or False,
					'actual_fees': student.actual_fees or False,
				}]],
				'user_id': student_user.id,
				'company_id': self.company_id.id,
				'partner_id': student_user.partner_id.id,
			})
			return details

	def enroll_student(self):
		for record in self:
			if record.register_id.max_count:
				total_admission = self.env['op.admission'].search_count(
					[('register_id', '=', record.register_id.id),
					 ('state', '=', 'done')])
				if not total_admission < record.register_id.max_count:
					msg = 'Max Admission In Admission Register :- (%s)' % (
						record.register_id.max_count)
					raise ValidationError(_(msg))
			if not record.student_id:
				vals = record.get_student_vals()
				vals['std_no'] = self.env['ir.sequence'].next_by_code('op.student')
				vals['admission_id'] = record.id
				record.partner_id = vals.get('partner_id')
				record.student_id = student_id = self.env[
					'op.student'].create(vals).id
				self.fees_detail_ids.update({
				'student_id': student_id,
				'level_id': record.level_id.id,
				})

			else:
				student_id = record.student_id.id
				record.student_id.write({
					'admission_id': record.id,
					'level_detail_ids': [[0, False, {
						'level_id':
							record.level_id and record.level_id.id or False,
						'batch_id':
							record.batch_id and record.batch_id.id or False,
						# 'fees_start_date': student.fees_start_date,
						'registration_fees': record.level_id.registration_fees or False,
						'study_fees': record.level_id.study_fees or False,
					}]],
				})
				self.fees_detail_ids.update({
				'student_id': record.student_id.id,
				'level_id': record.level_id.id,
				})
			
			record.write({
				'nbr': 1,
				'state': 'registration', #'done',
				'admission_date': fields.Date.today(),
				'student_id': student_id,
				'is_student': True,
			})
			reg_id = self.env['op.subject.registration'].create({
				'student_id': student_id,
				'batch_id': record.batch_id.id,
				'level_id': record.level_id.id,
				# 'min_unit_load': record.level_id.min_unit_load or 0.0,
				# 'max_unit_load': record.level_id.max_unit_load or 0.0,
				'state': 'draft',
			})
			if not record.phone or not record.mobile:
				raise UserError(
					_('Please fill in the mobile number'))
			reg_id.get_subjects()

	def confirm_rejected(self):
		self.state = 'reject'

	def create_invoice(self):
		if not self.fees_detail_ids:
			raise ValidationError(
				_('Sorry you must specify Fees Collection Details Firstly!!!'))
		self.fees_detail_ids.update({
			'student_id': self.student_id,
			'level_id': self.level_id.id,
		})
		inv_obj = self.env['account.move']
		partner_id = self.student_id.parent_id.name
		student = self.student_id
		account_id = False
		product = self.register_id.product_id

		if product.property_account_income_id:
			account_id = product.property_account_income_id.id
		if not account_id:
			account_id = product.categ_id.property_account_income_categ_id.id
		if not account_id:
			raise ValidationError(
				_('There is no income account defined for this product: "%s".'
				  'You may have to install a chart of account from Accounting'
				  ' app, settings menu.') % product.name)
		# if self.study_fees <= 0.00:
		# 	raise ValidationError(
		# 		_('The Study Fees must be greater than zero.'))
		if self.registration_fees <= 0.00:
			raise ValidationError(
				_('The Registration Fees must be greater than zero.'))
		else:
			study_amount = self.study_fees
			reg_amount = self.registration_fees
			name = product.name

		if self.study_fees > 0.00:
			invoice1 = inv_obj.create({
				'partner_id': partner_id.name,
				'move_type': 'out_invoice',
				'partner_id': partner_id.id,
				'ref': 'Study Fees for '+self.student_id.name,
				'invoice_date': fields.Date.today(),
				'student_id': student.id,
				'admission_id':self.id,
			})
			line_values = {'name': name,
						'account_id': account_id,
						'price_unit': study_amount,
						'quantity': 1.0,
						'discount': self.discount,
						'product_uom_id': product.uom_id.id,
						'product_id': product.id}
			invoice1.write({'invoice_line_ids': [(0, 0, line_values)]})
			# invoice1._compute_invoice_taxes_by_group()
			self.invoice_id1 = invoice1.id

		invoice2 = inv_obj.create({
			'partner_id': partner_id.name,
			'move_type': 'out_invoice',
			'partner_id': partner_id.id,
			'ref': 'Registration Fees for '+self.student_id.name,
			'invoice_date': fields.Date.today(),
			'student_id': student.id,
			'admission_id':self.id,
		})
		line_values = {'name': name,
					'account_id': account_id,
					'price_unit': reg_amount,
					'quantity': 1.0,
					'discount': 0.0,
					'product_uom_id': product.uom_id.id,
					'product_id': product.id}
		invoice2.write({'invoice_line_ids': [(0, 0, line_values)]})
		# invoice2._compute_invoice_taxes_by_group()
		self.invoice_id2 = invoice2.id
		self.state = 'done'

	def confirm_pending(self):
		self.state = 'pending'

	def confirm_to_draft(self):
		self.state = 'draft'

	def confirm_cancel(self):
		self.state = 'cancel'
		# if self.is_student and self.student_id.fees_detail_ids:
		#     self.student_id.fees_detail_ids.state = 'cancel'

	# def payment_process(self):
	#     self.state = 'fees_paid'

	def open_student(self):
		form_view = self.env.ref('openeducat_core.view_op_student_form')
		tree_view = self.env.ref('openeducat_core.view_op_student_tree')
		value = {
			'domain': str([('id', '=', self.student_id.id)]),
			'view_type': 'form',
			'view_mode': 'tree, form',
			'res_model': 'op.student',
			'view_id': False,
			'views': [(form_view and form_view.id or False, 'form'),
					  (tree_view and tree_view.id or False, 'tree')],
			'type': 'ir.actions.act_window',
			'res_id': self.student_id.id,
			'target': 'current',
			'nodestroy': True
		}
		self.state = 'done'
		return value

	@api.model
	def get_import_templates(self):
		return [{
			'label': _('Import Template for Admission'),
			'template': '/openeducat_admission/static/xls/op_admission.xls'
		}]
