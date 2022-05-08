

from odoo import models, fields, api, _


class OpLev(models.Model):
	_inherit = "op.student.level"

	discount = fields.Float()
	actual_fees = fields.Float('Fees After Discount',compute="_get_actual_fees")

	@api.depends('study_fees','discount')
	def _get_actual_fees(self):
		for rec in self:
			if rec.discount != 0.0:
				rec.actual_fees = rec.study_fees - ( (rec.study_fees * rec.discount)/100 )
			else:
				rec.actual_fees = rec.study_fees

class OpStudent(models.Model):
	_inherit = "op.student"

	parent_ids = fields.Many2many('op.parent', string='Parent')
	parent_id = fields.Many2one('op.parent',string="Student Parent")
	
	@api.model
	def create(self, vals):
		res = super(OpStudent, self).create(vals)
		if vals.get('parent_ids', False):
			for parent_id in res.parent_ids:
				if parent_id.user_id:
					user_ids = [x.user_id.id for x in parent_id.student_ids
								if x.user_id]
					parent_id.user_id.child_ids = [(6, 0, user_ids)]
		return res

	def write(self, vals):
		res = super(OpStudent, self).write(vals)
		if vals.get('parent_ids', False):
			user_ids = []
			if self.parent_ids:
				for parent in self.parent_ids:
					if parent.user_id:
						user_ids = [x.user_id.id for x in parent.student_ids
									if x.user_id]
						parent.user_id.child_ids = [(6, 0, user_ids)]
			else:
				user_ids = self.env['res.users'].search([
					('child_ids', 'in', self.user_id.id)])
				for user_id in user_ids:
					child_ids = user_id.child_ids.ids
					child_ids.remove(self.user_id.id)
					user_id.child_ids = [(6, 0, child_ids)]
		if vals.get('user_id', False):
			for parent_id in self.parent_ids:
				child_ids = parent_id.user_id.child_ids.ids
				child_ids.append(vals['user_id'])
				parent_id.name.user_id.child_ids = [(6, 0, child_ids)]
		self.clear_caches()
		return res

	def unlink(self):
		for record in self:
			if record.parent_ids:
				for parent_id in record.parent_ids:
					child_ids = parent_id.user_id.child_ids.ids
					child_ids.remove(record.user_id.id)
					parent_id.name.user_id.child_ids = [(6, 0, child_ids)]
		return super(OpStudent, self).unlink()

	def get_parent(self):
		action = self.env.ref('openeducat_parent.'
							  'act_open_op_parent_view').read()[0]
		action['domain'] = [('student_ids', 'in', self.ids)]
		return action


class OpSubjectRegistration(models.Model):
	_inherit = "op.subject.registration"

	@api.model
	def create(self, vals):
		if self.env.user.child_ids:
			raise exceptions.Warning(_('Invalid Action!\n Parent can not \
			create Subject Registration!'))
		return super(OpSubjectRegistration, self).create(vals)

	def write(self, vals):
		if self.env.user.child_ids:
			raise exceptions.Warning(_('Invalid Action!\n Parent can not edit \
			Subject Registration!'))
		return super(OpSubjectRegistration, self).write(vals)


# class OpStudentFeesDetails(models.Model):
# 	_inherit = "op.student.fees.details"


# 	# @api.depends('student_id','percentage')
# 	def _calc_fees(self):
# 		for rec in self:
# 			if rec.percentage > 0:
# 				rec.amount = rec.admission_id.actual_fees - ((rec.percentage * rec.admission_id.actual_fees)/100)
# 			else:
# 				rec.amount = 0
