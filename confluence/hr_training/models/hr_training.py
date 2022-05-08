# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class HrTrainingCourse(models.Model):
    _name = 'hr.training.course'
    _description = 'Training course'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char('Name',tracking=True,required=True)
    code = fields.Char('Code',tracking=True)
    description = fields.Html('Description',tracking=True)
    course_type = fields.Many2many('hr.training.course.type', string='Course Type',tracking=True)


class hrTrainingCourseType(models.Model):
    _name = 'hr.training.course.type'
    _description = 'training course type'

    name = fields.Char('Name',required=True)


class hrTraining(models.Model):
    _name = 'hr.training'
    _description = 'Training requests model '
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'combination'
    combination = fields.Char(compute='get_name')
    department = fields.Many2one('hr.department', string='Department',track_visibility='onchange', default=lambda self: self.env.user.department_id.id)
    course = fields.Many2one('hr.training.course', string='Course',track_visibility='onchange',required=True)
    employees = fields.Many2many('hr.employee',readonly=False, string='Employees',track_visibility='onchange')
    count = fields.Integer(string='Employees No', track_visibility='onchange')
    date_from = fields.Date(string='Date From', track_visibility='onchange',required=True)
    date_to = fields.Date(string='Date To', track_visibility='onchange',required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('confirmed', 'Confirmed'),
        ('executed', 'Executed'),
        ('cancel', 'Cancelled')], string='Status',
        track_visibility='onchange')
    
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

    @api.onchange('employees')
    def _get_count_employee(self):
        for rec in self:
            rec.count = len(rec.employees)
    # @api.model
    # def create(self,vals):
    #     active_model=  self.env.context.get('active_model')
    #     print(active_model)
    #     super(hrTraining, self).create(vals)
    #

    @api.depends('course', 'department')
    def get_name(self):
        for rec in self:
            if rec.department.name:
                rec.combination = rec.department.name + ':' + rec.course.name
            else:
                rec.combination = '\\' + ':' + rec.course.name



    def action_plan(self):
        self.state = 'planned'

    def action_confirm(self):
        if not self.employees:
            raise ValidationError(_('Please add Employees!'))
        self.state = 'confirmed'

    def action_execute(self):
        self.state = 'executed'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'
