# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# import pytz
from datetime import datetime, time
# from dateutil.rrule import rrule, DAILY
# from random import choice
# from string import digits
# from werkzeug.urls import url_encode
# from dateutil.relativedelta import relativedelta
# from collections import defaultdict

from odoo import api, fields, models, _
# from odoo.osv.query import Query
from odoo.exceptions import ValidationError, AccessError, UserError
# from odoo.osv import expression
# from odoo.tools.misc import format_date
# import date
import datetime

class FleetVehicleMovements(models.Model):
    _name = "fleet.vehicle.movements"
    _description = " Fleet Vehicle Movements confluence"

    @api.model
    def _get_default_employee(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_id.id

    name = fields.Char(string='Name')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)
    driver_id = fields.Many2one(related='vehicle_id.driver_id', string='Driver')
    requester = fields.Many2one('hr.employee', string='Request By',default=_get_default_employee)
    location = fields.Char(string='Location')
    date_from = fields.Datetime(string='From')
    date_to = fields.Datetime(string='To')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Wait GM Approval'),
        ('approve', 'Approve'),
    ], default='draft', string='Stage')
    sequence = fields.Char(string='Sequence',readonly=True,rack_visibility='onchange', index=True, default=lambda self: _( 'NEW' ))

    # create sequence
    @api.model
    def create(self, vals):
        result = super(FleetVehicleMovements, self).create(vals)
        if vals.get('sequence', 'New') == 'New':
            result.name = self.env['ir.sequence'].next_by_code(
                'fleet.vehicle.movements') or 'New'

        return result

    def action_confirm(self):

        self.write({'state': 'confirm'})

    def action_done(self):

        self.write({'state': 'approve'})


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"
    _description = " Fleet confluence"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Account Analytic')


class FleetVehicleLogServices(models.Model):
    _inherit = "fleet.vehicle.log.services"
    _rec_name = 'sequence'
    _description = "Fleet Vehicle Log Services"

    # name = fields.Char(string='Name')

    spare_parts_ids = fields.One2many('spare.parts.confluence','fleet_services_id', string='Spare Parts')
    confluence_services_ids = fields.One2many('services.confluence','fleet_services_confluence_id', string='Services')
    is_cars_insurance = fields.Boolean('Is Cars Insurance',defalut=False)
    # vehicle_analytic_account_id = fields.Many2one('vehicle_id.analytic_account_id', string='Receipt services', copy=False)
    move_id = fields.Many2one('account.move', string='Receipt services', copy=False)
    move_id2 = fields.Many2one('account.move', string='Receipt services', copy=False)
    sequence = fields.Char(string='Sequence',readonly=True,rack_visibility='onchange', index=True, default=lambda self: _( 'NEW' ))
    account_move_count = fields.Integer(string="Account Move", compute='_compute_account_move_ids')
    account_move_services_count = fields.Integer(string="Account Move", compute='_compute_account_services_move_ids')
    # state = fields.Selection(selection_add=[('draft','Draft'),('gm_approval','Wait GM Approval')],default='draft')
    amount = fields.Monetary('Cost',compute='compute_total_cost_of_servics',store=True)
    amount_cars_insurance = fields.Monetary('Cost')
    # sequence = fields.Char(string='Sequence',readonly=True,rack_visibility='onchange', index=True, default=lambda self: _( 'NEW' ))

    state = fields.Selection([
        ('draft', 'Draft'),
        ('gm_approval', 'Wait GM Approval'),
        ('todo', 'to do'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', string='Stage', group_expand='_expand_states')
    # create sequence
    @api.model
    def create(self,vals):
        result = super(FleetVehicleLogServices, self).create(vals)
        # month = datetime.strptime(result.date(field), '%Y-%m-%d').strftime('%m')
        if vals.get('sequence', 'New') == 'New':
            result.sequence = self.env['ir.sequence'].next_by_code(
                'fleet.vehicle.log.services') or 'New'

        return result

    @api.constrains('spare_parts_ids')
    def spare_parts_ids_constraint(self):
        for rec in self:
            if not rec.spare_parts_ids and rec.is_cars_insurance == False:
                raise UserError(_('Spare details in line must be Enter'))


    def action_running(self):
        """
        A method to running services
        """
        self.write({'state': 'gm_approval'})

    def action_done(self):
        """
        A method to done services
        """
        self.write({'state': 'done'})

    def set_to_new(self):
        """
        A method to done services
        """
        # self.write({'state': 'todo'})
        self.write({'state': 'new'})

    def action_cancelled(self):
        """
        A method to cancelled services
        """
        self.write({'state': 'cancelled'})



    def create_move_bi(self):
        move_obj = self.env['account.move']

        for services in self:

            lines = []
            lines_services = []
            for line in services.spare_parts_ids:

                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.quantity_spare,
                    'price_unit': line.cost_spare,
                    'analytic_account_id': services.vehicle_id.analytic_account_id.id,
                    'services_conflu_line_id': line.id,
                }))
            for rec in services.confluence_services_ids:

                lines.append((0, 0, {
                    'product_id': rec.product_id.id,
                    'name_services': rec.name,
                    'price_unit': rec.cost_services,
                    'services_confluence_line_id': rec.id,
                    'services_confluence': True,
                }))
            move_id = move_obj.create({
                'services_conflu_id':services.id,
                'date': fields.date.today(),
                'partner_id': services.vendor_id,
                # 'vehicle_id': services.vehicle_id,
                'ref': services.description,
                'move_type': 'in_invoice',
                'is_services': True,
                'invoice_line_ids': lines,
                # 'services_move_line_ids': lines_services,

            })
            # vehicle_id vehicle service_type_id  purchaser_id date
                # odometer amount 'account.move'
            services.move_id2 = move_id

    def create_insurance_move_bill(self):
        move_obj = self.env['account.move']
        lines = []
        for insurance in self:


            # for line in insurance.spare_parts_ids:

            lines.append((0, 0, {
                'name': insurance.description,
                'price_unit': insurance.amount_cars_insurance,
                'analytic_account_id': insurance.vehicle_id.analytic_account_id.id,
                'insurance_conflu_line_id': insurance.id,
            }))
            move_id = move_obj.create({
                'insurance_conflu_id':insurance.id,
                'date': fields.date.today(),
                'partner_id': insurance.vendor_id,
                # 'vehicle_id': services.vehicle_id,
                'move_type': 'in_invoice',
                'is_insurance': True,
                'invoice_line_ids': lines,

            })
            # vehicle_id vehicle service_type_id  purchaser_id date
                # odometer amount 'account.move'
            insurance.move_id = move_id


    def _compute_account_services_move_ids(self):
        for rec in self:
            account_move_ids = self.env['account.move'].search([('services_conflu_id', '=', rec.id)])
            rec.account_move_services_count = len(account_move_ids)
    def _compute_account_move_ids(self):
        for rec in self:
            account_move_ids = self.env['account.move'].search([('insurance_conflu_id', '=', rec.id)])
            rec.account_move_count = len(account_move_ids)

    def get_account_move_treeview(self):
        if self.account_move_count > 0:
            # view = self.env.ref('account.view_in_invoice_tree')
            view = self.env.ref('account.view_in_invoice_bill_tree')
            form_view = self.env.ref('account.view_move_form')
            return {
                'name': _('Bill'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'domain': [('insurance_conflu_id', '=', self.id)],
                'views': [(view.id, 'tree'), (form_view.id, 'form')],

            }
    def get_account_move_services_treeview(self):
        if self.account_move_services_count > 0:
            # view = self.env.ref('account.view_in_invoice_tree')
            view = self.env.ref('account.view_in_invoice_bill_tree')
            form_view = self.env.ref('account.view_move_form')
            return {
                'name': _('Bill'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'domain': [('services_conflu_id', '=', self.id)],
                'views': [(view.id, 'tree'), (form_view.id, 'form')],

            }
    @api.depends('confluence_services_ids','spare_parts_ids')
    def compute_total_cost_of_servics(self):

        for rec in self:
            rec.amount = 0
            sum_services_cost = 0
            sum_spare_cost = 0
            if rec.confluence_services_ids:
                for ser in rec.confluence_services_ids:
                    sum_services_cost +=ser.cost_services
            if rec.spare_parts_ids:
                for spr in rec.spare_parts_ids:
                    sum_spare_cost +=spr.cost_spare
            rec.amount = sum_services_cost + sum_spare_cost