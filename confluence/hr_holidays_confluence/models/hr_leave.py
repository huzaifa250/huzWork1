import logging
from collections import namedtuple, defaultdict
from datetime import datetime, timedelta, time
from pytz import timezone, UTC
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)
class Leave(models.Model):
	_inherit = 'hr.leave'

	is_permission = fields.Boolean()
	state = fields.Selection([
		('draft', 'To Submit'),
		('confirm', 'To Approve'),
		('human_resources', 'Human Resources'),
		('manager_approval', 'General Manager'),
		('refuse', 'Refused'),
		('validate1', 'Second Approval'),
		('validate', 'Approved')
		], string='Status', compute='_compute_state', store=True, tracking=True, copy=False, readonly=False,
		help="The status is set to 'To Submit', when a time off request is created." +
		"\nThe status is 'To Approve', when time off request is confirmed by user." +
		"\nThe status is 'Refused', when time off request is refused by manager." +
		"\nThe status is 'Approved', when time off request is approved by manager.")

	def first_confirm(self):
		if self.holiday_status_id.support_document:
			if not self.supported_attachment_ids:
				raise UserError(_('This time off required document, Please attach it .'))

		self.write({'state': 'human_resources'})

	def hr_confirm(self):
		self.write({'state': 'manager_approval'})

	def action_approve(self):
		# if validation_type == 'both': this method is the first approval approval
		# if validation_type != 'both': this method calls action_validate() below
		if any(holiday.state != 'manager_approval' for holiday in self):
			raise UserError(_('Time off request must be confirmed ("GM Approve") in order to approve it.'))

		current_employee = self.env.user.employee_id
		self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})

		# Post a second message, more verbose than the tracking message
		for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
			holiday.message_post(
				body=_(
					'Your %(leave_type)s planned on %(date)s has been accepted',
					leave_type=holiday.holiday_status_id.display_name,
					date=holiday.date_from
				),
				partner_ids=holiday.employee_id.user_id.partner_id.ids)

		self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
		if not self.env.context.get('leave_fast_create'):
			self.activity_update()
		return True

	def action_validate(self):
		current_employee = self.env.user.employee_id
		leaves = self._get_leaves_on_public_holiday()
		if leaves:
			raise ValidationError(_('The following employees are not supposed to work during that period:\n %s') % ','.join(leaves.mapped('employee_id.name')))

		if any(holiday.state not in ['confirm', 'validate1','manager_approval'] and holiday.validation_type != 'no_validation' for holiday in self):
			raise UserError(_('Time off request must be confirmed in order to approve it.'))

		self.write({'state': 'validate'})

		leaves_second_approver = self.env['hr.leave']
		leaves_first_approver = self.env['hr.leave']

		for leave in self:
			if leave.validation_type == 'both':
				leaves_second_approver += leave
			else:
				leaves_first_approver += leave

			if leave.holiday_type != 'employee' or\
				(leave.holiday_type == 'employee' and len(leave.employee_ids) > 1):
				if leave.holiday_type == 'employee':
					employees = leave.employee_ids
				elif leave.holiday_type == 'category':
					employees = leave.category_id.employee_ids
				elif leave.holiday_type == 'company':
					employees = self.env['hr.employee'].search([('company_id', '=', leave.mode_company_id.id)])
				else:
					employees = leave.department_id.member_ids

				conflicting_leaves = self.env['hr.leave'].with_context(
					tracking_disable=True,
					mail_activity_automation_skip=True,
					leave_fast_create=True
				).search([
					('date_from', '<=', leave.date_to),
					('date_to', '>', leave.date_from),
					('state', 'not in', ['cancel', 'refuse']),
					('holiday_type', '=', 'employee'),
					('employee_id', 'in', employees.ids)])

				if conflicting_leaves:
					# YTI: More complex use cases could be managed in master
					if leave.leave_type_request_unit != 'day' or any(l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
						raise ValidationError(_('You can not have 2 time off that overlaps on the same day.'))

					# keep track of conflicting leaves states before refusal
					target_states = {l.id: l.state for l in conflicting_leaves}
					conflicting_leaves.action_refuse()
					split_leaves_vals = []
					for conflicting_leave in conflicting_leaves:
						if conflicting_leave.leave_type_request_unit == 'half_day' and conflicting_leave.request_unit_half:
							continue

						# Leaves in days
						if conflicting_leave.date_from < leave.date_from:
							before_leave_vals = conflicting_leave.copy_data({
								'date_from': conflicting_leave.date_from.date(),
								'date_to': leave.date_from.date() + timedelta(days=-1),
								'state': target_states[conflicting_leave.id],
							})[0]
							before_leave = self.env['hr.leave'].new(before_leave_vals)
							before_leave._compute_date_from_to()

							# Could happen for part-time contract, that time off is not necessary
							# anymore.
							# Imagine you work on monday-wednesday-friday only.
							# You take a time off on friday.
							# We create a company time off on friday.
							# By looking at the last attendance before the company time off
							# start date to compute the date_to, you would have a date_from > date_to.
							# Just don't create the leave at that time. That's the reason why we use
							# new instead of create. As the leave is not actually created yet, the sql
							# constraint didn't check date_from < date_to yet.
							if before_leave.date_from < before_leave.date_to:
								split_leaves_vals.append(before_leave._convert_to_write(before_leave._cache))
						if conflicting_leave.date_to > leave.date_to:
							after_leave_vals = conflicting_leave.copy_data({
								'date_from': leave.date_to.date() + timedelta(days=1),
								'date_to': conflicting_leave.date_to.date(),
								'state': target_states[conflicting_leave.id],
							})[0]
							after_leave = self.env['hr.leave'].new(after_leave_vals)
							after_leave._compute_date_from_to()
							# Could happen for part-time contract, that time off is not necessary
							# anymore.
							if after_leave.date_from < after_leave.date_to:
								split_leaves_vals.append(after_leave._convert_to_write(after_leave._cache))

					split_leaves = self.env['hr.leave'].with_context(
						tracking_disable=True,
						mail_activity_automation_skip=True,
						leave_fast_create=True,
						leave_skip_state_check=True
					).create(split_leaves_vals)

					split_leaves.filtered(lambda l: l.state in 'validate')._validate_leave_request()

				values = leave._prepare_employees_holiday_values(employees)
				leaves = self.env['hr.leave'].with_context(
					tracking_disable=True,
					mail_activity_automation_skip=True,
					leave_fast_create=True,
					no_calendar_sync=True,
					leave_skip_state_check=True,
				).create(values)

				leaves._validate_leave_request()

		leaves_second_approver.write({'second_approver_id': current_employee.id})
		leaves_first_approver.write({'first_approver_id': current_employee.id})

		employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
		employee_requests._validate_leave_request()
		if not self.env.context.get('leave_fast_create'):
			employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
		return True


class HrEmployeeBase(models.AbstractModel):
	_inherit = "hr.employee.base"

	current_leave_state = fields.Selection(compute='_compute_leave_status', string="Current Time Off Status",
		selection=[
			('draft', 'New'),
			('confirm', 'Waiting Approval'),
			('human_resources', 'Human Resources'),
			('manager_approval', 'General Manager'),
			('refuse', 'Refused'),
			('validate1', 'Waiting Second Approval'),
			('validate', 'Approved'),
			('cancel', 'Cancelled')
		])