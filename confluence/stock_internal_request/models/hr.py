# -*- coding: utf-8 -*-

from odoo import api, fields, models


# class HrEmployeePublic(models.Model):
#     _inherit = 'hr.employee.public'
#
#     location_dest_id = fields.Many2one(readonly=True)


class Employee(models.Model):
    _inherit = 'hr.employee'

    location_dest_id = fields.Many2one('stock.location', "Destination Location", required=False,
                                       tracking=True)


class Department(models.Model):
    _inherit = 'hr.department'

    location_dest_id = fields.Many2one('stock.location', "Destination Location")
