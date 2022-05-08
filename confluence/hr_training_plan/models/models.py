
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import date


class HrTrainingExecution(models.Model):
    _name = 'hr.training.execution'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    name = fields.Char()

    start_date = fields.Date(track_visibility='onchange', string="Start Date")
    end_date = fields.Date(track_visibility='onchange', string="End Date")
    line_ids = fields.One2many('hr.training', 'training_execution', string='Plan Execution')
    voucher = fields.Many2one('account.move', string='Voucher',copy=False)
    vendor = fields.Many2one('res.partner', string='Vendor')
    payment_type = fields.Selection([
        ('by_total', 'Total'),
        ('by_employee', 'Per employee')], string='Payment Type',
        default='by_total',
        track_visibility='onchange',
        select=True)

    no_employee = fields.Integer(string='No Employee', compute='_compute_no_employee')
    voucher_amount_per_employee = fields.Float(string='Voucher Amount Per Employee')
    total_voucher_amount = fields.Float(string='Voucher Amount')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    account_id = fields.Many2one('account.account', string='Account')
    course = fields.Many2one('hr.training.course', string='Course')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done','Done')], default='draft')
    employee_evaluation_template = fields.Many2one("survey.survey", string="Employee Evaluation Template")
    manager_evaluation_template = fields.Many2one("survey.survey", string="Manager Evaluation Template")

    def action_confirm(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_('Please add training details!'))
        self.action_fetch()
        self.write({'state': 'confirm'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'hr.training.execution') or 'New'
        result = super(HrTrainingExecution, self).create(vals)
        return result

    def _compute_no_employee(self):
        for rec in self:
            rec.no_employee = sum(rec.line_ids.mapped('count'))

    def action_execute(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_('There are no lines, please fetch it first!!'))
        for line in self.line_ids:
            line.action_execute()
        if not self.account_id.id and not self.env.company.training_account_id.id:
            raise ValidationError(_('Pleace add accounts!'))
        if not self.account_analytic_id.id and not self.env.company.training_account_analytic_id.id:
            raise ValidationError(_('No analytic accounts!'))

        amount = 0.0
        if self.payment_type == 'by_total':
            amount = self.total_voucher_amount 
        else:
            amount = self.no_employee * self.voucher_amount_per_employee

        if amount > 0.0:
            move = self.env['account.move'].create({
                'move_type': 'in_receipt',
                'partner_id': self.vendor.id,
                # 'journal_id': 2,
                'invoice_line_ids': [
                    (0, None, {
                        'quantity': 1,
                        'price_unit':  amount,
                        'name': self.course.name,
                        'account_id': self.account_id.id if self.account_id.id else self.env.company.training_account_id.id,
                        'analytic_account_id': self.account_analytic_id.id if self.account_analytic_id.id else self.env.company.training_account_analytic_id.id,
                    }),
                ]})
            self.send_notification_move_created(move)
            self.voucher = move
            self.state = 'done'
        else:
            raise ValidationError(_('Voucher Amount must be > 0'))



    def send_notification_move_created(self,move):
        if move:
            body = ('<strong>Move Alert<br/>%sThe Voucher is Create<br/>click here: </strong>') % (move.name)
            body += '<a href=# data-oe-model=account.move data-oe-id=%d>%s</a>' % (move.id, move.name)
            message = self.env['mail.message']
            group_id = self.env.ref('account.group_account_manager')
            user_ids = self.env['res.users'].search([('groups_id', '=', group_id.id)])
            admin_group_id = self.env.ref('base.user_admin')
            admin_user_id = self.env['res.users'].search([('groups_id', '=', admin_group_id.id)],limit=1)
            for user in user_ids:
                vals = {
                    'message_type': 'notification',
                    'author_id': admin_user_id.partner_id.id,
                    'body': body,
                    'model': 'account.move',
                    'res_id': move.id,
                    'partner_ids': [(6, 0, [user.partner_id.id])]
                }
                message_id = message.create(vals)
                notification_id = self.env['mail.notification'].create({
                    'mail_message_id': message_id.id,
                    'notification_type': 'inbox',
                    'res_partner_id': user.partner_id.id})
        

    def action_fetch(self):
        trainings = self.env['hr.training'].search(
            [('date_from', '>=', self.start_date), ('date_to', '<=', self.end_date), ('course', '=', self.course.id),
             ('state', '=', 'confirmed'),('training_execution','=',False)])
        self.write({'line_ids': trainings.ids})

    def send_employee_survey(self):
        if not self.employee_evaluation_template:
            raise ValidationError(_('Please add Employee Evaluation Template !!'))
        template = self.env.ref('survey.mail_template_user_input_invite', raise_if_not_found=False)
        partners = []
        for line in self.line_ids:
            for employee in line.employees:
                partners.append(employee.address_home_id.id)
        local_context = dict(
            self.env.context,
            default_survey_id=self.employee_evaluation_template.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            notif_layout='mail.mail_notification_light',
            default_partner_ids=partners,
            default_training_id=self.id,
            )

        return {
            'name':'Send Evaluation Form',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'survey.invite',
            'target': 'new',
            'context': local_context
        }

    def send_manager_survey(self):
        if not self.manager_evaluation_template:
            raise ValidationError(_('Please add Employee Evaluation Template !!'))
        template = self.env.ref('survey.mail_template_user_input_invite', raise_if_not_found=False)
        partners = []
        for line in self.line_ids:
            for employee in line.employees:
                partners.append(employee.user_partner_id.id)
        local_context = dict(
            self.env.context,
            default_survey_id=self.manager_evaluation_template.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            notif_layout='mail.mail_notification_light',
            default_partner_ids=partners,
            default_training_id=self.id,
        )
        return {
            'name': 'Send Evaluation Form',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'survey.invite',
            'target': 'new',
            'context': local_context
        }


    def action_employees_answers(self):
        action = self.env['ir.actions.act_window']._for_xml_id('survey.action_survey_user_input')
        ctx = dict(self.env.context)
        ctx.update({'search_default_survey_id': self.employee_evaluation_template.id,
                    'search_default_completed': 1,
                    # 'search_default_not_test': 1,
                    })
        action['context'] = ctx
        action['domain'] = [('training_id', '=', self.id)]
        return action

    def action_managers_answers(self):
        action = self.env['ir.actions.act_window']._for_xml_id('survey.action_survey_user_input')
        ctx = dict(self.env.context)
        ctx.update({'search_default_survey_id': self.manager_evaluation_template.id,
                    'search_default_completed': 1,
                    # 'search_default_not_test': 1
                    })
        action['context'] = ctx
        action['domain'] = [('training_id', '=', self.id)]
        return action

    def send_notification_to_hr_in_chatterr(self):
        res = self.env['hr.training.execution'].search([])
        for rec in res:
            if rec.end_date:
                num_days = (fields.Date.today() - rec.end_date).days
                if num_days < 4 or num_days == 3:
                    hr_manag_group_id = self.env.ref('base_custom.group_general_manager')
                    hr_officer_group_id = self.env.ref('hr.group_hr_user')
                    hr_user = rec.env['res.users'].search(['|', ('groups_id', '=', hr_manag_group_id.id), ('groups_id', '=', hr_officer_group_id.id)])
                    notification_ids = []
                    for line in hr_user:
                        notification_ids.append((0, 0, {
                            'res_partner_id': line.partner_id.id,
                            'notification_type': 'inbox'}))
                    rec.message_post(body=_('%s rajaa') % rec.name,message_type='notification',subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,notification_ids=notification_ids)





class HrTrainingPlan(models.Model):
    _name = 'hr.training.plan'
    _description = 'hr_training_plan.hr_training_plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence'

    sequence = fields.Char("Name", index=True, required=True, default="New", copy=False)
    start_date = fields.Date(track_visibility='onchange',string="Start Date", default=lambda self: fields.Date.to_string(date.today().replace(day=1, month=1)))
    end_date = fields.Date(track_visibility='onchange',string="End Date", default=lambda self: fields.Date.to_string(date.today().replace(day=31, month=12)))
    department = fields.Many2one('hr.department', string='Department', track_visibility='onchange',
                                 default=lambda self: self.env.user.employee_id.department_id.id , required=True)
    line_ids = fields.One2many('hr.training', 'training_plan', string='Plan Details')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved')], string='Status',
        default='draft',
        track_visibility='onchange')
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
    @api.constrains('start_date','end_date')
    def _check_training_plan_period(self):
        old_name = self.env['hr.training.plan'].search([('start_date', '>=', self.start_date),('start_date','<=',self.end_date),('end_date', '<=', self.end_date),('end_date','>=',self.start_date),('id','!=',self.id),('department','=',self.department.id)])
        if old_name:
            raise UserError(_('You Cannot create training plan in same period!'))


    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'hr.training.plan') or 'New'
        result = super(HrTrainingPlan, self).create(vals)
        return result

    def action_confirm(self):
        if len(self.line_ids) == 0:
            raise UserError(_('Cannot confirm plan with empty lines')) 
        else:
            self.state = 'confirmed'

    def action_approve(self):
        self.state = 'approved'

    def action_draft(self):
        self.write({'state': 'draft'})
    # def send_notification_to_hr_in_chatter(self):
    #
    #     logistic_manger_group = self.env['res.groups'].search([('name','=', 'Logistic Manger')])
    #     logistic_officer_group = self.env['res.groups'].search([('name','=', 'Logistic Officer')])
    #     notification_users =self.env['res.users'].search(['|', ('groups_id', '=',logistic_manger_group.id), ('groups_id', '=',logistic_officer_group.id)])
    #     notification_ids = []
    #
    #     for line in notification_users:
    #         notification_ids.append((0, 0, {'res_partner_id': line.partner_id.id,'notification_type': 'inbox'}))
    #     self.message_post(body=_('The status of shipment record %s has changed') % self.name , message_type='notification',subtype_xmlid = 'mail.mt_comment',author_id = self.env.user.partner_id.id,notification_ids = notification_ids)


    # def action_approve(self):
    #     self.state = 'approved'

        # @api.model
    # def create(self, vals):
    #     print(vals['line_ids'])
    #     vals.update({'line_ids': [({'department': self.department.id})]})
    #     # vals.update({'line_ids': [({'department': dep})]})
    #     super(HrTrainingPlan, self).create(vals)
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100


class ResPartner(models.Model):
    _inherit = 'res.partner'
    is_training_center = fields.Boolean(string='Is Training Center')


class ResCompany(models.Model):
    _inherit = 'res.company'

    training_account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    training_account_id = fields.Many2one('account.account', string='Account')


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    training_account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                                   related='company_id.training_account_analytic_id', readonly=False)
    training_account_id = fields.Many2one('account.account', string='Account', related='company_id.training_account_id',
                                          readonly=False)



class hrTrainingInherit(models.Model):
    _inherit = 'hr.training'


    department = fields.Many2one('hr.department', string='Department',track_visibility='onchange', default=lambda self: self.env.user.employee_id.department_id.id)
    employees = fields.Many2many('hr.employee',readonly=False, string='Employees',track_visibility='onchange')
    training_plan = fields.Many2one('hr.training.plan')
    training_execution = fields.Many2one('hr.training.execution')

    @api.constrains('employees','course')
    def constrains_training_course(self):
        for rec in self:
            trainings = self.env['hr.training'].search([('date_from', '>=', rec.date_from),('date_from','<=',rec.date_to),('date_to', '<=', rec.date_to),('date_to','>=',rec.date_from),('course', '=', rec.course.id),('id', '!=', rec.id)])
               
            for training in trainings:
                employees_line_ids = training.employees.filtered(lambda x:x.id in rec.employees.ids)
                if employees_line_ids:
                    raise UserError('Employee should not have the same cource at same period!')


    @api.constrains('employees')
    def _check_employee_constrains(self):
        for rec in self:
            if not rec.employees:
                raise UserError('You Can Not Create Training Without At Least One Employee!')

        