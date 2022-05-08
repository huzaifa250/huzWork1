

from odoo import api, fields, models,_

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	transportation = fields.Boolean(default=False)


class HrPayslipEmployees(models.TransientModel):
	_inherit = 'hr.payslip.employees'

	def compute_sheet(self):
		self.ensure_one()
		if not self.env.context.get('active_id'):
			from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
			end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
			today = fields.date.today()
			first_day = today + relativedelta(day=1)
			last_day = today + relativedelta(day=31)
			if from_date == first_day and end_date == last_day:
				batch_name = from_date.strftime('%B %Y')
			else:
				batch_name = _('From %s to %s', format_date(self.env, from_date), format_date(self.env, end_date))
			payslip_run = self.env['hr.payslip.run'].create({
				'name': batch_name,
				'date_start': from_date,
				'date_end': end_date,
			})
		else:
			payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

		employees = self.with_context(active_test=False).employee_ids
		print('++++++++++++++++++++ len',len(employees))
		print('++++++++++++++++++++ employees',employees)
		if payslip_run.transportation:
			employees = employees.filtered(lambda emp: (emp.contract_id.staff_type != False and emp.contract_id.transportation_international != 0.0) or (emp.contract_id.staff_type != False and emp.contract_id.transportation != 0.0))
			# search(['|',('contract_id.transportation_international','!=',0.0),('contract_id.transportation','!=',0.0)])
			print('++++++++++++++++++++ employees',employees)
			print('++++++++++++++++++++ after len',len(employees))

		if not employees:
			raise UserError(_("You must select employee(s) to generate payslip(s)."))

		#Prevent a payslip_run from having multiple payslips for the same employee
		employees -= payslip_run.slip_ids.employee_id
		success_result = {
			'type': 'ir.actions.act_window',
			'res_model': 'hr.payslip.run',
			'views': [[False, 'form']],
			'res_id': payslip_run.id,
		}
		if not employees:
			return success_result

		payslips = self.env['hr.payslip']
		Payslip = self.env['hr.payslip']

		contracts = employees._get_contracts(
			payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
		).filtered(lambda c: c.active)
		contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
		work_entries = self.env['hr.work.entry'].search([
			('date_start', '<=', payslip_run.date_end),
			('date_stop', '>=', payslip_run.date_start),
			('employee_id', 'in', employees.ids),
		])
		self._check_undefined_slots(work_entries, payslip_run)

		if(self.structure_id.type_id.default_struct_id == self.structure_id):
			work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
			if work_entries._check_if_error():
				return {
					'type': 'ir.actions.client',
					'tag': 'display_notification',
					'params': {
						'title': _('Some work entries could not be validated.'),
						'sticky': False,
					}
				}


		default_values = Payslip.default_get(Payslip.fields_get())
		payslips_vals = []
		for contract in contracts:
			values = dict(default_values, **{
				'name': _('New Payslip'),
				'employee_id': contract.employee_id.id,
				'credit_note': payslip_run.credit_note,
				'payslip_run_id': payslip_run.id,
				'date_from': payslip_run.date_start,
				'date_to': payslip_run.date_end,
				'contract_id': contract.id,
				'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
			})
			payslips_vals.append(values)
		payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
		payslips._compute_name()
		payslips.compute_sheet()
		payslip_run.state = 'verify'

		return success_result