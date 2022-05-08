

from odoo import api, models


class TRANSPORTDETAILS(models.AbstractModel):
	_name = 'report.hr_payroll_confluence.report_transportation_template'


	@api.model
	def _get_report_values(self, docids, data=None):
		docs = self.env['hr.payslip.run'].browse(docids)

		query = """ select emp.name,hpl.code,hpl.amount,wo.number_of_days,wo.is_paid,emp.contract_id from hr_payslip hp
					left join hr_payslip_line hpl on slip_id = hp.id
					left join hr_employee emp on emp.id = hp.employee_id
					left join hr_payslip_worked_days wo on wo.payslip_id = hp.id
					where hp.payslip_run_id = %s """ % docids[0]

		self.env.cr.execute(query)
		result = self._cr.fetchall()

		### create dict every key contain employee name and the values contain his details 
		slip_dict = {}
		for rec in result:
			if rec[0] in slip_dict:
				val = [rec[1],rec[2],rec[3],rec[4],rec[5]]
				slip_dict[rec[0]].append(val)
			else:
				slip_dict[rec[0]] = [[rec[1],rec[2],rec[3],rec[4],rec[5]]]

		### get totals of work days and absence days
		for key in slip_dict:
			code = ''
			amount = 0.0
			work_days = 0.0
			absent_days = 0.0
			contract_amount = 0.0
			for item in slip_dict[key]:
				code = item[0]
				amount = item[1]
				if item[3]:
					work_days += item[2]
				elif not item[3]:
					absent_days += item[2]
				contract_amount = item[4]
			contract = self.env['hr.contract'].search([('id','=',contract_amount)])
			if contract.staff_type == 'local_staff':
				contract_amount = contract.transportation_fixed
			elif contract.staff_type == 'international_staff':
				contract_amount = contract.transportation_international
			slip_dict[key] = [[code,amount,work_days,absent_days,contract_amount]]

		print('++++++++++++++++++slip_dict ',slip_dict)
		deserved_amount = 0.0
		for key in slip_dict:
			key_list = [0,0,0,0]
			for val in slip_dict[key]:
				if val[0] == 'TRANS_ALLOW':
					key_list[0] = val[4]
					key_list[1] = val[2]
					key_list[2] = val[3]
					key_list[3] = val[1]
					deserved_amount += key_list[3]

			slip_dict[key] = key_list

		return {
			  'doc_ids': docids,
			  'doc_model': 'op.parent',
			  'docs': docs,
			  'data': data,
			  'slip_dict':slip_dict,
			  'total':deserved_amount,
			  'company_id': self.env.user.company_id,
		}
