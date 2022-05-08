
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class contract_allowances(models.Model):
    _name = 'contract.allowances'

    name = fields.Char(default='Allowances')
    salary = fields.Float('Salary(%)',required=True)
    allowance = fields.Float('Allowance(%)',required=True)
    basic = fields.Float('Basic(%)',required=True)
    cola = fields.Float('Cola(%)',required=True)
    subsistence = fields.Float('Subsistence(%)',required=True)
    clothing = fields.Float('clothing(%)',required=True)
    transportation = fields.Float('Transportation(%)',required=True)
