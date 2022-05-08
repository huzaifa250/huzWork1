from odoo import api, fields, models,_

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	days_work = fields.Float(compute="_get_days")
	days_absence = fields.Float(compute="_get_days",string="Days To Deduct")
	transportation = fields.Boolean(related="payslip_run_id.transportation")

	def _get_days(self):
		self.days_work = 0
		self.days_absence = 0
		if self.worked_days_line_ids:
			days = days_work = days_absence = 0
			for line in self.worked_days_line_ids:
				days += line.number_of_days
				if line.is_paid:
					days_work += line.number_of_days
				if not line.is_paid:
					days_absence += line.number_of_days
			self.days_work = days_work
			self.days_absence = days_absence


# 	def compute_sheet(self):
# 		"""
# 		inherit from compute_sheet to get sick leaves from payslip
# 		"""
# 		return super(HrPayslip, self).compute_sheet()


class HrPayrollStructure(models.Model):
	_inherit = 'hr.payroll.structure'

	@api.model
	def _get_default_rule_ids(self):
		return []

	rule_ids = fields.One2many(
		'hr.salary.rule', 'struct_id',
		string='Salary Rules', default=_get_default_rule_ids)



class HrContract(models.Model):
	_inherit = "hr.contract"
	_description = " HR Contract confluence"

	@api.depends('wage')
	def compute_salary_details(self):
		print('++++++++ in custom')
		for rec in self:
			if rec.staff_type == 'local_staff':
				obj_ids = self.env['contract.allowances'].search([]).ids
				if obj_ids:
					pers_conf = self.env['contract.allowances'].browse(max(obj_ids))
					rec.allowance = rec.wage * pers_conf.allowance
					rec.salary = rec.wage * pers_conf.salary
					rec.basic = rec.wage * pers_conf.basic
					rec.cola = rec.wage * pers_conf.cola
					rec.subsistence = rec.wage * pers_conf.subsistence
					rec.clothing = rec.wage * pers_conf.clothing
					rec.transportation = rec.wage * pers_conf.transportation
				else:
					rec.allowances = rec.wage * 0.6
					rec.salary = rec.wage * 0.4
					rec.basic = rec.salary * 0.6
					rec.cola = rec.salary * 0.2
					rec.subsistence = rec.salary * 0.1
					rec.clothing = rec.salary * 0.05
					rec.transportation = rec.salary * 0.05
			else:
				rec.allowances = 0.0
				rec.salary = 0.0
				rec.basic = 0.0
				rec.cola = 0.0
				rec.subsistence = 0.0
				rec.clothing = 0.0
				rec.transportation = 0.0
			
class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'
	_description = 'Salary Rule'

	use_type = fields.Selection(string='Use Type', selection=[('general', 'General'), ('special', 'Special')], default='general')
	