
from odoo import models, fields, api, _


class OpAdmission(models.Model):
	_inherit = "op.admission"

	parent_id = fields.Many2one('op.parent',required=True,string="Student Parent")
	student_sibing_no = fields.Integer(compute='get_student_sibing_no',store=True)
	discount = fields.Float(compute='get_discount',store=True)
	actual_fees = fields.Float('Fees After Discount',compute="_get_actual_fees",store=True)

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

	def create_invoice(self):
		inv_obj = self.env['account.move']
		partner_id = self.parent_id.name
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
		if self.study_fees <= 0.00:
			raise ValidationError(
				_('The Study Fees must be greater than zero.'))
		if self.registration_fees <= 0.00:
			raise ValidationError(
				_('The Registration Fees must be greater than zero.'))
		else:
			study_amount = self.study_fees
			reg_amount = self.registration_fees
			name = product.name

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
		invoice1._compute_tax_totals_json()
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
		invoice2._compute_tax_totals_json()
		self.invoice_id2 = invoice2.id
		self.state = 'done'
	