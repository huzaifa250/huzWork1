

from odoo import api, models


class ParentStatement(models.AbstractModel):
	_name = 'report.confluence_reports.parent_statement_template'

	@api.model
	def _get_report_values(self, docids, data=None):
		docs = self.env['op.parent'].browse(docids)
		parent = self.env['op.parent'].browse(docids)
		student_ids = parent.student_ids
		childs = []
		total_fees = 0
		paid_fees = 0
		remain_fees = 0
		payments = []
		for student in student_ids:
			child = [student.name,student.level_id.name]
			admission = self.env['op.admission'].search([('student_id','=',student.id)])
			level_fees = self.env['op.student.level'].search([
				('student_id','=',student.id),('level_id','=',student.level_id.id)])
			child.append(level_fees.actual_fees+admission.registration_fees)
			total_fees += level_fees.actual_fees+admission.registration_fees
			childs.append(child)
		
			fees_payments = self.env['account.payment'].search([('student_id','=',student.id)])
			for fee in fees_payments:
				if fee.state == 'posted':
					paid_fees += fee.amount

				payment = [fee.date,fee.name,fee.currency_id.symbol,fee.amount,fee.amount_words]
				payments.append(payment)

		remain_fees = total_fees - paid_fees

		return {
			  'doc_ids': docids,
			  'doc_model': 'op.parent',
			  'docs': docs,
			  'data': data,
			  'childs': childs,
			  'total_fees':total_fees,
			  'paid_fees': paid_fees,
			  'remain_fees': remain_fees,
			  'payments':payments,
		}
