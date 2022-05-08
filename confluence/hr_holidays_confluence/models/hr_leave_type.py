from odoo import api, fields, models,_

class LeaveTypes(models.Model):
	_inherit = 'hr.leave.type'

	is_annual = fields.Boolean(default=False)
	annual_days = fields.Float('Time Off Days')


class LeaveAllocation(models.Model):
	_inherit = 'hr.leave.allocation'


	def _auto_annual_allocation(self):
		now = fields.Date.today()
		contracts = self.env['hr.contract'].search([('state','=','open')])
		annual_leaves = self.env['hr.leave.type'].search([('is_annual','=',True)])
		if annual_leaves:
			for annual in annual_leaves:
				for contract in contracts:
					date_start = contract.date_start
					if (now - date_start).days == 365:
						print('+++++++++++++++++++ contract',contract.name)
						employee = self.env['hr.employee'].search([('contract_id','=',contract.id)])
						allocation_dict = {
							'name': annual.name,
							'holiday_status_id': annual.id,
							'number_of_days': annual.annual_days,
							'holiday_type': 'employee',
							'employee_id': employee.id,
						}
						new_allocation = self.env['hr.leave.allocation'].create(allocation_dict)
						new_allocation.sudo().action_confirm()
						new_allocation.sudo().action_validate()
						print('+++++++++++ new_allocation',new_allocation)

		return True
