# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OpStudentlevel(models.Model):
	_name = "op.student.level"
	_description = "Student Grade Details"
	_inherit = "mail.thread"
	_rec_name = 'student_id'

	student_id = fields.Many2one('op.student', 'Student', ondelete="cascade", tracking=True)
	level_id = fields.Many2one('op.level', 'Grade', required=True, tracking=True)
	batch_id = fields.Many2one('op.batch', 'Batch', required=True, tracking=True)
	roll_number = fields.Char('Roll Number', tracking=True)
	subject_ids = fields.Many2many('op.subject', string='Subjects')
	academic_years_id = fields.Many2one('op.academic.year', 'Academic Year')
	academic_term_id = fields.Many2one('op.academic.term', 'Terms')
	study_fees = fields.Float()
	registration_fees = fields.Float()

	_sql_constraints = [
		('unique_name_roll_number_id',
		 'unique(roll_number,level_id,batch_id,student_id)',
		 'Roll Number & Student must be unique per Batch!'),
		('unique_name_roll_number_level_id',
		 'unique(roll_number,level_id,batch_id)',
		 'Roll Number must be unique per Batch!'),
		('unique_name_roll_number_student_id',
		 'unique(student_id,level_id,batch_id)',
		 'Student must be unique per Batch!'),
	]

	@api.model
	def get_import_templates(self):
		return [{
			'label': _('Import Template for Student level Details'),
			'template': '/openeducat_core/static/xls/op_student_level.xls'
		}]

	@api.onchange('level_id')
	def onchange_level(self):
		if self.level_id:
			if self.level_id.study_fees:
				self.study_fees = self.level_id.study_fees
			if self.level_id.registration_fees:
				self.registration_fees = self.level_id.registration_fees



class OpStudent(models.Model):
	_name = "op.student"
	_description = "Student"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_inherits = {"res.partner": "partner_id"}

	first_name = fields.Char('First Name', size=128, translate=True)
	middle_name = fields.Char('Middle Name', size=128, translate=True)
	last_name = fields.Char('Last Name', size=128, translate=True)
	forth_name = fields.Char('Forth Name', size=128, translate=True)
	birth_date = fields.Date('Birth Date')
	blood_group = fields.Selection([
		('A+', 'A+ve'),
		('B+', 'B+ve'),
		('O+', 'O+ve'),
		('AB+', 'AB+ve'),
		('A-', 'A-ve'),
		('B-', 'B-ve'),
		('O-', 'O-ve'),
		('AB-', 'AB-ve')
	], string='Blood Group')
	gender = fields.Selection([
		('m', 'Male'),
		('f', 'Female'),
		('o', 'Other')
	], 'Gender', required=True, default='m')
	nationality = fields.Many2one('res.country', 'Nationality')
	emergency_contact = fields.Many2one('res.partner', 'Emergency Contact')
	visa_info = fields.Char('Visa Info', size=64)
	id_number = fields.Char('ID Card Number', size=64)
	partner_id = fields.Many2one('res.partner', 'Partner',
								 required=True, ondelete="cascade")
	user_id = fields.Many2one('res.users', 'User', ondelete="cascade")
	gr_no = fields.Char("GR Number", size=20)
	category_id = fields.Many2one('op.category', 'Category')
	level_detail_ids = fields.One2many('op.student.level', 'student_id',
										'Grade Details',
										tracking=True)
	active = fields.Boolean(default=True)
	level_id = fields.Many2one('op.level',compute="get_level",store=True,string="Grade")
	academic_years_id = fields.Many2one('op.academic.year',
						'Academic Year',
						tracking=True,required=True)
	academic_term_id = fields.Many2one('op.academic.term',
									   'Academic Terms',
									   tracking=True,required=True)
	batch_id = fields.Many2one(
		'op.batch', 'Batch')
	std_no = fields.Char()
	
	_sql_constraints = [(
		'unique_gr_no',
		'unique(gr_no)',
		'GR Number must be unique per student!'
	)]

	
	@api.onchange('first_name', 'middle_name', 'last_name','forth_name')
	def _onchange_name(self):
		self.name = str(self.first_name) + " " + str(
			self.middle_name) + " " + str(self.last_name) + " " + str(self.forth_name)

	@api.constrains('birth_date')
	def _check_birthdate(self):
		for record in self:
			if record.birth_date > fields.Date.today():
				raise ValidationError(_(
					"Birth Date can't be greater than current date!"))

	@api.model
	def get_import_templates(self):
		return [{
			'label': _('Import Template for Students'),
			'template': '/openeducat_core/static/xls/op_student.xls'
		}]

	def create_student_user(self):
		user_group = self.env.ref("base.group_portal") or False
		users_res = self.env['res.users']
		for record in self:
			if not record.user_id:
				user_id = users_res.create({
					'name': record.name,
					'partner_id': record.partner_id.id,
					'login': record.email,
					'groups_id': user_group,
					'is_student': True,
					'tz': self._context.get('tz'),
				})
				record.user_id = user_id
