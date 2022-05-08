
from odoo import Command,models, fields, api, _
from odoo.exceptions import ValidationError
from . import amount_to_ar


class OpStudent(models.Model):
	_inherit = "op.student"
	

	# level_id2 = fields.Many2one('op.level',string="Grade")
	level_id = fields.Many2one('op.level',compute="get_level",store=True,string="Grade")
	fees_detail_ids = fields.One2many('op.student.fees.details',
									  'student_id',
									  string='Fees Collection Details',
									  # domain=[('level_id','=',level_id)]
									  )
	invoice_ids = fields.One2many('account.move','student_id')
	total_invoiced = fields.Integer(compute='compute_total_invoiced')
	admission_id = fields.Many2one('op.admission')
	# level_visible = fields.Boolean(compute="get_domain")

	# def get_domain(self):
	# 	print('++++++++++++ in domain',self.level_id.id)
	# 	self.level_visible = True
	# 	if self.level_visible:
	# 		print('########################### in domain')
	# 		return {'domain':{'fees_detail_ids':('level_id','=',self.level_id.id)}}


	@api.depends('level_detail_ids')
	def get_level(self):
		for rec in self:
			if rec.level_detail_ids:
				std_level = self.env['op.student.level'].browse(max(rec.level_detail_ids.ids))
				rec.level_id = std_level.level_id.id or False
			else:
				rec.level_id = False

	def compute_total_invoiced(self):
		for student in self:
			inv_ids = []
			for invoice in student.invoice_ids:
				if invoice.move_type == 'out_invoice':
					inv_ids += [invoice.id]

			student.total_invoiced = len(inv_ids)

	def action_view_invoice(self):
		result = self.env.ref('account.action_move_out_invoice_type')
		fees = result and result.id or False
		result = self.env['ir.actions.act_window'].browse(fees).read()[0]
		inv_ids = []
		for student in self:
			inv_ids += [invoice.id for invoice in student.invoice_ids]
			result['context'] = {'default_student_id': student.id}
		result['domain'] = \
				"[('id','in',[" + ','.join(map(str, inv_ids)) + "]),('move_type','=','out_invoice')]"
		return result

	def _auto_draft_payment(self):
		installments_to_pay = self.fees_detail_ids.search([('date','=',fields.Date.today()),('paid','=',False),('payment_id','=',False)])
		pay_method_line_id = self.env['account.payment.method.line'].search([('payment_type', '=', 'inbound')],limit=1)
		if installments_to_pay:
			for installment in installments_to_pay:
				payment_vals = {
					'date': installment.date,
					'amount': installment.amount,
					'payment_type': 'inbound',
					'ref': installment.student_id.name + ' Fees Installment',
					'journal_id': self.env['account.journal'].search([('type','=','sale')]).id or False,
					'partner_id': installment.student_id.parent_id.name.id,
					'payment_method_line_id': pay_method_line_id.id,
					'student_id':installment.student_id.id
				}
				payment_id = self.env['account.payment'].create(payment_vals)
				installment.payment_id = payment_id
				if payment_id:
					ids = installment.search([])
					self.notification_method(ids)


	def notification_method(self,ids):
		for rec in ids:
			if rec.payment_id:
				message_id = self.env['mail.message'].create({
					'message_type': 'notification',
					'body': 'Today you must receive fees installment from (%s) ralated to his child (%s), Please follow up your payments' % (rec.student_id.parent_id.name.name,rec.student_id.name),
					'subject': 'Notify for Receive Fees Installment',
					'model': rec._name,
					'res_id': rec.id,
					'partner_ids': [3],
					'author_id': self.env.user.partner_id.id,
				})
				self.env['mail.notification'].create({
					'mail_message_id': message_id.id,
					'res_partner_id': 3,
					'notification_type': 'inbox',
				})
				print('+++++++++++++++ message send success ####################')


class OpStudentFeesDetails(models.Model):
	_name = "op.student.fees.details"
	_description = "Student Fees Details"
	_rec_name = 'student_id'

	student_id = fields.Many2one('op.student', 'Student')
	date = fields.Date('Submit Date')
	percentage = fields.Float('Perc(%)')
	amount = fields.Float('Fees Amount', compute='_calc_fees')
	level_id = fields.Many2one('op.level',string="Grade")
	payment_id = fields.Many2one('account.payment',store=True)
	paid = fields.Boolean(default=False,compute='_get_status')
	admission_id = fields.Many2one('op.admission')
	re_registration_id = fields.Many2one('re.registration')
	lable = fields.Char('installments')
	dedlines = fields.Date('Deadline')

	@api.depends('payment_id')
	def _get_status(self):
		for rec in self:
			if rec.payment_id:
				rec.paid = True
			else:
				rec.paid = False

	@api.depends('percentage')
	def _calc_fees(self):
		for rec in self:
			if rec.percentage > 0:
				rec.amount = rec.admission_id.actual_fees - ((rec.percentage * rec.admission_id.actual_fees)/100)
			else:
				rec.amount = 0

class Invoices(models.Model):
	_inherit = 'account.move'

	student_id = fields.Many2one('op.student')
	admission_id = fields.Many2one('op.admission')
	re_registration_id = fields.Many2one('re.registration')

class Payments(models.Model):
	_inherit = 'account.payment'

	student_id = fields.Many2one('op.student')
	year = fields.Char(default=lambda self : fields.Date.today().year)
	amount_words = fields.Char(string='Amount in Words', readonly=True, default=False, copy=False,
								  compute='_compute_text', translate=True)
	company_id = fields.Many2one(
		'res.company', string='Company',
		default=lambda self: self.env.user.company_id)

	@api.depends('amount')
	def _compute_text(self):
		if self.currency_id.symbol == 'ج.س.':
			self.amount_words = amount_to_ar.amount_to_text_ar(self.amount,'جنيه', 'قرش')
		elif self.currency_id.symbol == '$':
			self.amount_words = amount_to_ar.amount_to_text_ar(self.amount,'دولار', 'سنت')
		else:
			self.amount_words = ''