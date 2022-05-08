
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReRegistration(models.Model):
	_name = "re.registration"
	_inherit = "mail.thread"
	_rec_name = "parent_id"

	request_date = fields.Date(
		'Request Date', required=True, 
		default=lambda self: fields.Date.today(),states={'done': [('readonly', True)]})
	parent_id = fields.Many2one(
		'op.parent', 'Parent',states={'done': [('readonly', True)]})
	student_ids = fields.One2many('student.re.registration','re_registration_id', string='Student(s)'
		,states={'done': [('readonly', True)]})
	validity_date = fields.Date(
		'Validity Date', required=True,states={'done': [('readonly', True)]})
	fees_detail_ids = fields.One2many('op.student.fees.details',
									  're_registration_id',
									  string='Fees Collection Details'
									  ,states={'done': [('readonly', True)]})
	coordinator_name = fields.Char(states={'done': [('readonly', True)]})
	admission_office_name = fields.Char(states={'done': [('readonly', True)]})
	state = fields.Selection(selection=[
		('draft','Draft'),('wait_list','Waitting List'),
		('register','Register'),('done','Done'),('cancel','Cancelled')],default='draft')
	invoice_ids = fields.One2many('account.move','student_id',states={'done': [('readonly', True)]})
	total_invoiced = fields.Integer(compute='compute_total_invoiced')


	def compute_total_invoiced(self):
		count = 0
		for student in self.student_ids:
			if student.invoice_id1:
				count += 1
			if student.invoice_id2:
				count += 1
		self.total_invoiced = count

	@api.onchange('parent_id')
	def onchange_parent(self):
		for rec in self:
			rec.student_ids = False
			rec.invoice_ids = False
			rec.fees_detail_ids = False
			if rec.parent_id:
				for student in rec.parent_id.student_ids:
					rec.write({
						'student_ids': [(0, 0, {
							'student_id':student.id,
							'academic_years_id':student.academic_years_id,
							'level_id': student.level_id,
							'class_id': student.class_id,
							'batch_id': student.batch_id
							})]
						})

	def to_wait_list(self):
		self.state = 'wait_list'

	def to_register(self):
		self.state = 'register'

	def to_done(self):
		self.state = 'done'

	def to_cancel(self):
		self.state = 'cancel'

	def create_invoice(self):
		self.invoice_ids = False
		if not self.fees_detail_ids:
			raise ValidationError(
				_('Sorry you must specify Fees Details Firstly!!!'))
		if not self.student_ids:
			raise ValidationError(
				_('Sorry you must specify Students Firstly!!!'))
		inv_obj = self.env['account.move']
		partner_id = self.parent_id.name
		account_id = False
		
		for line in self.student_ids:
			if line.final_decision == 'accept':
				student = line.student_id.id
				product = line.register_id.product_id
				discount = 0

				########### get student discount #############
				parent_child_ids = self.env['op.admission'].search([('parent_id','=',self.parent_id.id),('state','not in',['draft','reject','pending','cancel'])])
				childs_no = len(parent_child_ids)
				print('++++++++++++++++ childs_no',childs_no)
				if childs_no <= 4:
					admission_id = line.student_id.admission_id
					if admission_id:
						discount = admission_id.discount
					else:
						discount = self.env['op.admission'].search([('student_id','=',line.student_id.id)],limit=1).discount
				else:
					discount = 0

				if product.property_account_income_id:
					account_id = product.property_account_income_id.id
				if not account_id:
					account_id = product.categ_id.property_account_income_categ_id.id
				if not account_id:
					raise ValidationError(
						_('There is no income account defined for this product: "%s".'
						  'You may have to install a chart of account from Accounting'
						  ' app, settings menu.') % product.name)

				if line.new_level_id.registration_fees <= 0.00:
					raise ValidationError(
						_('The Registration Fees must be greater than zero.'))
				else:
					study_amount = line.new_level_id.study_fees
					reg_amount = line.new_level_id.registration_fees
					name = product.name

				if not line.new_class_id:
					raise ValidationError(
						_('Sorry you must specify New Class for (%s)') % line.student_id.name)
				if not line.new_batch_id:
					raise ValidationError(
						_('Sorry you must specify New Batch for (%s)') % line.student_id.name)

				if line.new_level_id.study_fees > 0.00:
					invoice1 = inv_obj.create({
						'partner_id': partner_id.name,
						'move_type': 'out_invoice',
						'partner_id': partner_id.id,
						'ref': 'Study Fees for '+line.student_id.name,
						'invoice_date': fields.Date.today(),
						'student_id': student,
						're_registration_id': self.id,
					})
					line_values = {'name': name,
								'account_id': account_id,
								'price_unit': study_amount,
								'quantity': 1.0,
								'discount': discount,
								'product_uom_id': product.uom_id.id,
								'product_id': product.id}
					invoice1.write({'invoice_line_ids': [(0, 0, line_values)]})
					line.invoice_id1 = invoice1.id

				invoice2 = inv_obj.create({
					'partner_id': partner_id.name,
					'move_type': 'out_invoice',
					'partner_id': partner_id.id,
					'ref': 'Registration Fees for '+line.student_id.name,
					'invoice_date': fields.Date.today(),
					'student_id': student,
					're_registration_id': self.id,
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
				line.invoice_id2 = invoice2.id

				################### update student record ##################

				line.student_id.write({
					'academic_years_id': line.register_id and line.register_id.academic_years_id.id or False,
					'academic_term_id': line.register_id and line.register_id.academic_term_id.id or False,
					'class_id': line.new_class_id and line.new_class_id.id or False,
					'level_detail_ids': [[0, False, {
						'level_id':
							line.new_level_id and line.new_level_id.id or False,
						'class_id':
							line.new_class_id and line.new_class_id.id or False,
						'batch_id':
							line.new_batch_id and line.new_batch_id.id or False,
						'study_fees': line.new_level_id.study_fees or 00,
						'discount': discount,
						'academic_years_id': line.register_id and line.register_id.academic_years_id.id or False,
						'academic_term_id': line.register_id and line.register_id.academic_term_id.id or False,
						'subject_ids': [(6, 0, line.new_level_id.subject_ids.ids)],
					}]],
				})
				self.fees_detail_ids.update({
				'student_id': line.student_id.id,
				'level_id': line.new_level_id.id,
				})

				reg_id = self.env['op.subject.registration'].create({
					'student_id': line.student_id.id,
					'batch_id': line.new_batch_id.id,
					'level_id': line.new_level_id.id,
					'compulsory_subject_ids': [(6, 0, line.new_level_id.subject_ids.ids)],
					'state': 'draft',
				})
		self.state = 'done'

	def action_view_invoice(self):
		result = self.env.ref('account.action_move_out_invoice_type')
		fees = result and result.id or False
		result = self.env['ir.actions.act_window'].browse(fees).read()[0]
		inv_ids = []
		for student in self.student_ids:
			inv_ids += [student.invoice_id1.id,student.invoice_id2.id]
		result['context'] = {'default_re_registration_id': self.id}
		result['domain'] = \
				"[('id','in',[" + ','.join(map(str, inv_ids)) + "])]"
		return result
					
		

class StudentsReg(models.Model):
	_name = "student.re.registration"

	student_id = fields.Many2one(
		'op.student', 'Student')
	academic_years_id = fields.Many2one('op.academic.year',
						'Academic Year', tracking=True)
	level_id = fields.Many2one(
		'op.level', 'Grade')
	class_id = fields.Many2one(
		'op.classroom', 'Class')
	batch_id = fields.Many2one(
		'op.batch', 'Batch')
	register_id = fields.Many2one(
		'op.admission.register', 'Admission Register')
	new_academic_years_id = fields.Many2one('op.academic.year',
						'New Academic Year', tracking=True)
	new_level_id = fields.Many2one(
		'op.level', 'New Grade')
	new_class_id = fields.Many2one(
		'op.classroom', 'New Class')
	new_batch_id = fields.Many2one(
		'op.batch', 'New Batch')

	student_behavior = fields.Selection(selection=[
		('perfect','Perfect'),('middle','Middle'),('weak','Weak')],
		string='Behavior',default='middle')
	student_commitment = fields.Selection(selection=[
		('perfect','Perfect'),('middle','Middle'),('weak','Weak')],
		string='Commitment',default='middle')
	final_decision = fields.Selection(selection=[
		('accept','Accepted'),('reject','Rejected')],default='accept',required=True)
	reason = fields.Text()
	re_registration_id = fields.Many2one('re.registration')
	invoice_id1 = fields.Many2one('account.move', 'Study Fees Invoice')
	invoice_id2 = fields.Many2one('account.move', 'Registration Fees Invoice')

	@api.onchange('register_id')
	def onchange_register(self):
		for rec in self:
			if rec.register_id:
				rec.new_level_id = rec.register_id.level_id
				rec.new_academic_years_id = rec.register_id.academic_years_id

		