

from odoo import api, models


class SALARYDETAILS(models.AbstractModel):
	_name = 'report.hr_payroll_confluence.report_salary_details_template'


	@api.model
	def _get_report_values(self, docids, data=None):
		docs = self.env['hr.payslip.run'].browse(docids)

		query = """ select emp.name,hpl.code,hpl.amount from hr_payslip hp
					left join hr_payslip_line hpl on slip_id = hp.id
					left join hr_employee emp on emp.id = hp.employee_id
					where hp.payslip_run_id = %s order by hpl.code """ % docids[0]

		self.env.cr.execute(query)
		result = self._cr.fetchall()

		slip_dict = {}
		for rec in result:
			if rec[0] in slip_dict:
				val = [rec[1],rec[2]]
				slip_dict[rec[0]].append(val)
			else:
				slip_dict[rec[0]] = [[rec[1],rec[2]]]

		total = 0.0
		for key in slip_dict:
			key_list = [0,0,0,0,0,0,0,0,0]
			for val in slip_dict[key]:
				if val[0] == 'SALARY':
					key_list[0] = val[1]
				if val[0] == 'BASIC':
					key_list[1] = val[1]
				if val[0] == 'COLA':
					key_list[2] = val[1]
				if val[0] == 'SUB':
					key_list[3] = val[1]
				if val[0] == 'CLOTH':
					key_list[4] = val[1]
				if val[0] == 'TRANS':
					key_list[5] = val[1]
				if val[0] == 'SI':
					key_list[6] = val[1]
				if val[0] == 'TAX':
					key_list[7] = val[1]
				if val[0] == 'NET':
					key_list[8] = val[1]
					total += val[1]
				
			slip_dict[key] = key_list

		return {
			  'doc_ids': docids,
			  'doc_model': 'op.parent',
			  'docs': docs,
			  'data': data,
			  'slip_dict':slip_dict,
			  'total':total,
			  'company_id': self.env.user.company_id,
		}

