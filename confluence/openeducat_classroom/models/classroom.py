# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenEduCat Inc
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<http://www.openeducat.org>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import models, fields, api


class OpClassroom(models.Model):
    _name = "op.classroom"
    _description = "Classroom"

    name = fields.Char('Name', size=16, required=True)
    code = fields.Char('Code', size=16, required=True)
    level_id = fields.Many2one('op.level', 'level',required=True)
    batch_id = fields.Many2one('op.batch', 'Batch')
    capacity = fields.Integer(string='No of Person')
    facilities = fields.One2many('op.facility.line', 'classroom_id',
                                 string='Facility Lines')
    asset_line = fields.One2many('op.asset', 'asset_id',
                                 string='Asset')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_classroom_code',
         'unique(code)', 'Code should be unique per classroom!')]

    @api.onchange('level_id')
    def onchange_level(self):
        self.batch_id = False


class Levels(models.Model):
    _inherit = "op.level"

    class_ids = fields.One2many('op.classroom','level_id')

class StdLevels(models.Model):
    _inherit = "op.student.level"

    class_id = fields.Many2one('op.classroom')

# class Admission(models.Model):
#     _inherit = "op.admission"

#     class_id = fields.Many2one('op.classroom')


class Students(models.Model):
    _inherit = "op.student"

    class_id = fields.Many2one('op.classroom',compute="get_class")

    @api.depends('level_detail_ids')
    def get_class(self):
        for rec in self:
            if rec.level_detail_ids:
                std_level = self.env['op.student.level'].browse(max(rec.level_detail_ids.ids))
                # rec.level_id = std_level.level_id.id or False
                rec.class_id = std_level.class_id.id or False
                # rec.batch_id = std_level.batch_id.id or False
            else:
                # rec.level_id = False
                rec.class_id = False
                # rec.batch_id = False