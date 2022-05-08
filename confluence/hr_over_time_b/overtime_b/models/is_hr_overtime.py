from datetime import datetime
from dateutil import relativedelta
import time

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
import babel


class HrOvertime(models.Model):
    _name = 'hr.overtime'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # employee_id = fields.Many2one('hr.employee')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, readonly=True)

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    def _is_department_manager(self):
        for rec in self:
            if rec.name.parent_id.user_id.id == rec.env.user.id or rec.name.manager_id.user_id.id == rec.env.user.id:
                rec.is_department_manager = True
            else:
                rec.is_department_manager = False

    name = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True)
    department_id = fields.Many2one('hr.department', related="name.department_id", readonly=True,
                                    string="Department")
    is_working_day = fields.Boolean(string="Working Day")
    is_holiday = fields.Boolean(string="Holiday Day")
    is_eid_day = fields.Boolean(string="Eid Day")
    is_department_manager = fields.Boolean(string="Is Department Manager", compute="_is_department_manager")
    hour = fields.Float(string="Work Hours", required=True, compute='_get_amount')
    employee_salary = fields.Float(string="Employee Salary")
    hours = fields.Integer(string="Hours", required=True)
    minute = fields.Integer(string="Minute", required=True)
    amount = fields.Float(string="Overtime Amount", compute='_get_amount')
    overtime_date = fields.Date(string="Date", required=True)
    comment = fields.Text(string="Comments")
    employee_account = fields.Many2one('account.account', string="Debit Account")
    overtime_account = fields.Many2one('account.account', string="Credit Account")
    analytic_debit_account_id = fields.Many2one('account.analytic.account',
                                                # related='department_id.analytic_debit_account_id', readonly=True,
                                                string="Analytic Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('approve', 'Approved'),
        ('done', 'Done'), ('paid', 'Paid'),
        ('refuse', 'Refused'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    @api.depends('employee_salary', 'hour', 'minute')
    def _get_amount(self):
        for overtime in self:
            overtime.amount = 0.0
            overtime.hour = 0.0
            if overtime.employee_salary:
                hours_float = 0.0
                min = 0.0
                hour = overtime.hours
                minute = overtime.minute
                min = float(minute) / 60
                hours_float = hour + min
                overtime.hour = hours_float
                overtime_hour = 0.0
                employee_hour_cost = 0.0
                employee_salary = overtime.name.contract_id.wage
                employee_basic = employee_salary * .45
                employee_cola = employee_salary * .2
                employee_hour_cost = (employee_basic + employee_cola) / 240
                # print('++++++++++++employee_hour_cost ',employee_hour_cost)
                if overtime.is_working_day:
                    overtime_hour = hours_float * 1.5
                if overtime.is_holiday:
                    overtime_hour = hours_float * 2
                if overtime.is_eid_day:
                    overtime_hour = hours_float * 2.5
                # print('++++++++++++overtime_hour ', overtime_hour)
                overtime.amount = overtime_hour * employee_hour_cost

    @api.onchange('name')
    def _onchange_employee_d(self):
        if self.name:
            self.employee_salary = self.name.contract_id.wage

    @api.constrains('is_working_day', 'is_holiday', 'is_eid_day')
    def determine_overtime_day(self):
        for rec in self:
            if not rec.is_working_day:
                if not rec.is_holiday:
                    if not rec.is_eid_day:
                        raise Warning(
                            _("Please determine work day of overtime is it work day or holiday day or Eid day!"))
            if not rec.is_holiday:
                if not rec.is_working_day:
                    if not rec.is_eid_day:
                        raise Warning(
                            _("Please determine work day of overtime is it work day or holiday day or Eid day!"))
            if not rec.is_eid_day:
                if not rec.is_working_day:
                    if not rec.is_holiday:
                        raise Warning(
                            _("Please determine work day of overtime is it work day or holiday day or Eid day!"))

    def hr_validate(self):
        for rec in self:
            rec.state = 'approve'

    def action_sent(self):
        for rec in self:
            rec.state = 'sent'

    def finance1_validate(self):
        for rec in self:
            rec.state = 'done'

    def action_paid(self):
        for rec in self:
            rec.state = 'paid'

    def unlink(self):
        if any(self.filtered(lambda hr_overtime: hr_overtime.state not in ('draft', 'refuse'))):
            raise UserError(_('You cannot delete a Overtime which is not draft or refused!'))
        return super(HrOvertime, self).unlink()

    import datetime

    def finance_validate(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        created_move_ids = []
        for overtime in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            overtime_hour = 0.0
            overtime_request_date = overtime.overtime_date
            # company_currency = overtime.name.company_id.currency_id.id
            # current_currency = self.env.user.company_id.currency_id.id
            # hour = overtime.hour
            # employee_salary = overtime.name.contract_id.wage
            # employee_basic = employee_salary*.45
            # employee_cola = employee_salary*.2
            # employee_hour_cost = (employee_basic + employee_cola)/240
            # if overtime.is_working_day:
            #     overtime_hour = hour*1.5
            #
            # if overtime.is_holiday:
            #     overtime_hour = hour*2
            # amount = overtime_hour*employee_hour_cost
            amount = overtime.amount
            overtime_name = 'Overtime For ' + overtime.name.name
            # reference = overtime_name.name
            journal_id = overtime.journal_id.id
            move_dict = {
                'narration': overtime_name,
                'ref': '/',
                'journal_id': journal_id,
                'date': overtime_request_date,
            }
            debit_line = (0, 0, {
                'name': overtime_name,
                'partner_id': False,
                'account_id': overtime.employee_account.id,
                'journal_id': journal_id,
                'date': overtime_request_date,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                'analytic_account_id': overtime.analytic_debit_account_id.id,
                'tax_line_id': 0.0,
            })
            line_ids.append(debit_line)
            debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
            credit_line = (0, 0, {
                'name': overtime_name,
                'partner_id': False,
                'account_id': overtime.overtime_account.id,
                'journal_id': journal_id,
                'date': overtime_request_date,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                'analytic_account_id': False,
                'tax_line_id': 0.0,
            })
            line_ids.append(credit_line)
            credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_journal_credit = overtime.journal_id.default_credit_account_id.id
                if not acc_journal_credit:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                        overtime.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_journal_credit,
                    'journal_id': journal_id,
                    'date': overtime_request_date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_journal_deit = overtime.journal_id.default_debit_account_id.id
                if not acc_journal_deit:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                        overtime.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_journal_deit,
                    'journal_id': journal_id,
                    'date': overtime_request_date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            overtime.write({'move_id': move.id, 'date': overtime_request_date})
            move.post()
        self.state = 'done'

    def overtime_reset(self):
        for rec in self:
            rec.state = 'draft'

    def overtime_refuse(self):
        for rec in self:
            rec.state = 'refuse'

    @api.constrains('minute')
    def _minute_limit(self):
        for rec in self:
            if rec.minute >= 60:
                raise Warning(_("Please enter minutes less than 60!"))

    @api.constrains('hour')
    def _total_hour_limit(self):
        for rec in self:
            if rec.hour <= 0.0:
                raise Warning(_("Overtime hours mut be greater than 0 please check it!"))


class OvertimeLine(models.Model):
    _name = 'overtime.line'

    name = fields.Many2one('hr.employee', string='Employee')
    employee_hour_salary = fields.Float(string="Hour Value", compute='compute_hour_value')
    employee_salary = fields.Float(string="Basic Salary", compute='compute_hour_value')
    overtime_month = fields.Float(string='Hours Total')
    overtime_month_value = fields.Float(string='Amount')
    total_work_hour = fields.Float(string='Total Normal Hour')
    total_work_overtime = fields.Float(string='Normal Hour * 1.5')
    total_holiday_hour = fields.Float(string='Total Holiday Hour')
    total_holiday_overtime = fields.Float(string='Holiday Hour * 2')
    overtime_line_id = fields.Many2one('hr.overtime.month', string='Overtime Month', ondelete='cascade')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, readonly=True)

    @api.depends('name')
    def compute_hour_value(self):
        for rec in self:
            rec.employee_salary = 0.0
            rec.employee_hour_salary = 0.0
            if rec.name:
                salary = rec.name.contract_id.wage
                rec.employee_salary = salary * 0.65
                rec.employee_hour_salary = salary * 0.65 / 240


class HrOvertimeMonth(models.Model):
    _name = 'hr.overtime.month'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Overtime')
    date_from = fields.Date(string='Date From', required=True,
                            default=time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    # overtime = fields.Float("Monthly Overtime", readonly=True, compute='compute_month_overtime_hours', store=True)
    overtime_line_ids = fields.One2many('overtime.line', 'overtime_line_id', string='Overtime Month')
    debit_account = fields.Many2one('account.account', string="Debit Account")
    credit_account = fields.Many2one('account.account', string="Credit Account")
    analytic_debit_account_id = fields.Many2one('account.analytic.account',
                                                string="Analytic Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('refuse', 'Refused')
    ], string="State", default='draft', track_visibility='onchange', copy=False, )
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, readonly=True)

    @api.onchange('date_from')
    def onchange_date(self):
        for x in self:
            ttyme = x.date_from
            locale = self.env.context.get('lang', 'en_US')
            x.name = _('Overtime for %s') % (
                tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))

    @api.depends('date_from', 'date_to')
    def compute_overtime_month(self):
        for x in self:
            ttyme = x.date_from
            locale = self.env.context.get('lang', 'en_US')
            x.name = _('Overtime for %s') % (
                tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
            overtime_obj = x.env['hr.overtime']
            overtime_line_obj = x.env['overtime.line']
            employee_obj = x.env['hr.employee'].search([])
            x.overtime_line_ids.unlink()
            for employee in employee_obj:
                employee_id = employee.id
                overtime_ids = overtime_obj.search(
                    [('overtime_date', '>=', x.date_from), ('overtime_date', '<=', x.date_to),
                     ('name', '=', employee_id), ('state', '=', 'done')], order='name')
                total_overtime = 0.0
                sum_hours = 0.0
                sum_work_hours = 0.0
                sum_holiday_hours = 0.0
                total_amount = 0.0
                overtime_holiday = 0.0
                overtime_working = 0.0
                total_work_overtime = 0.0
                total_holiday_overtime = 0.0
                total_hours = 0.0
                for overtime in overtime_ids:
                    # employee = overtime.name.id
                    basic_salary = employee.contract_id.wage * 0.65
                    employee_salary_hour = basic_salary / 240
                    if overtime.is_working_day:
                        sum_work_hours += overtime.hour
                    if overtime.is_holiday:
                        sum_holiday_hours += overtime.hour
                    total_work_overtime = sum_work_hours * 1.5
                    total_holiday_overtime = sum_holiday_hours * 2
                    total_hours = total_work_overtime + total_holiday_overtime
                    total_amount = total_hours * employee_salary_hour
                    # if sum_hours != 0.0:
                    #     if overtime.is_working_day:
                    #         overtime_working = sum_hours * employee_salary_hour * 1.5
                    #     if overtime.is_holiday:
                    #         overtime_holiday = sum_hours * employee_salary_hour * 2
                    #     total_overtime = overtime_working + overtime_holiday
                if total_hours != 0.0:
                    overtime_line_ids = overtime_line_obj.create({
                        'name': employee_id,
                        'total_work_hour': sum_work_hours,
                        'total_work_overtime': total_work_overtime,
                        'total_holiday_hour': sum_holiday_hours,
                        'total_holiday_overtime': total_holiday_overtime,
                        'overtime_month': total_hours,
                        'overtime_month_value': total_amount,
                        'overtime_line_id': x.id})
        return True

    def confirm_overtime(self):
        for rec in self:
            rec.state = 'confirm'

    def finance_validate(self):
        for rec in self:
            precision = self.env['decimal.precision'].precision_get('Payroll')
            move_obj = self.env['account.move']
            move_line_obj = self.env['account.move.line']
            currency_obj = self.env['res.currency']
            created_move_ids = []
            for overtime in self:
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                overtime_hour = 0.0
                amount = 0.0
                overtime_request_date = datetime.now()
                for line in rec.overtime_line_ids:
                    amount += line.overtime_month_value
                # company_currency = overtime.name.company_id.currency_id.id
                # current_currency = self.env.user.company_id.currency_id.id
                # hour = overtime.hour
                # employee_salary = overtime.name.contract_id.wage
                # employee_basic = employee_salary*.45
                # employee_cola = employee_salary*.2
                # employee_hour_cost = (employee_basic + employee_cola)/240
                # if overtime.is_working_day:
                #     overtime_hour = hour*1.5
                #
                # if overtime.is_holiday:
                #     overtime_hour = hour*2
                # amount = overtime_hour*employee_hour_cost
                # amount = overtime.amount
                overtime_name = 'Overtime For ' + rec.name
                # reference = overtime_name.name
                journal_id = rec.journal_id.id
                move_dict = {
                    'narration': overtime_name,
                    'ref': '/',
                    'journal_id': journal_id,
                    'date': overtime_request_date,
                }
                debit_line = (0, 0, {
                    'name': overtime_name,
                    'partner_id': False,
                    'account_id': rec.debit_account.id,
                    'journal_id': journal_id,
                    'date': overtime_request_date,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'analytic_account_id': rec.analytic_debit_account_id.id,
                    'tax_line_id': 0.0,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                credit_line = (0, 0, {
                    'name': overtime_name,
                    'partner_id': False,
                    'account_id': rec.credit_account.id,
                    'journal_id': journal_id,
                    'date': overtime_request_date,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'analytic_account_id': False,
                    'tax_line_id': 0.0,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    acc_journal_credit = overtime.journal_id.default_credit_account_id.id
                    if not acc_journal_credit:
                        raise UserError(
                            _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                                overtime.journal_id.name))
                    adjust_credit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_journal_credit,
                        'journal_id': journal_id,
                        'date': overtime_request_date,
                        'debit': 0.0,
                        'credit': debit_sum - credit_sum,
                    })
                    line_ids.append(adjust_credit)

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    acc_journal_deit = overtime.journal_id.default_debit_account_id.id
                    if not acc_journal_deit:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                            overtime.journal_id.name))
                    adjust_debit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_journal_deit,
                        'journal_id': journal_id,
                        'date': overtime_request_date,
                        'debit': credit_sum - debit_sum,
                        'credit': 0.0,
                    })
                    line_ids.append(adjust_debit)
                move_dict['line_ids'] = line_ids
                move = self.env['account.move'].create(move_dict)
                overtime.write({'move_id': move.id})
                move.post()
                for line in rec.overtime_line_ids:
                    overtime_obj = self.env['hr.overtime']
                    overtime_ids = overtime_obj.search(
                        [('overtime_date', '>=', self.date_from), ('overtime_date', '<=', self.date_to),
                         ('name', '=', line.name.id), ('state', '=', 'done')], order='name')
                    for pay in overtime_ids:
                        pay.action_paid()
            rec.state = 'done'

    def unlink(self):
        if any(self.filtered(lambda overtime_month: overtime_month.state not in ('draft', 'refuse'))):
            raise UserError(_('You cannot delete a Overtime which is not draft or refused!'))
        return super(HrOvertimeMonth, self).unlink()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    overtime_id = fields.Many2one('hr.overtime', string="Overtime")
