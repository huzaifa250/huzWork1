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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StudentMigrate(models.TransientModel):
    """ Student Migration Wizard """
    _name = "student.migrate"
    _description = "Student Migrate"

    date = fields.Date('Date', required=True, default=fields.Date.today())
    level_from_id = fields.Many2one('op.level', 'From Level', required=True)
    level_to_id = fields.Many2one('op.level', 'To Level', required=True)
    batch_id = fields.Many2one('op.batch', 'To Batch')
    optional_sub = fields.Boolean("Optional Subjects")
    student_ids = fields.Many2many(
        'op.student', string='Student(s)', required=True)

    @api.constrains('level_from_id', 'level_to_id')
    def _check_admission_register(self):
        for record in self:
            if record.level_from_id == record.level_to_id:
                raise ValidationError(
                    _("From Level must not be same as To Level!"))

            if record.level_from_id.parent_id:
                if record.level_from_id.parent_id != \
                        record.level_to_id.parent_id:
                    raise ValidationError(_(
                        "Can't migrate, As selected levels don't \
                        share same parent level!"))
            else:
                raise ValidationError(
                    _("Can't migrate, Proceed for new admission"))

    @api.onchange('level_from_id')
    def onchange_level_id(self):
        self.student_ids = False

    def student_migrate_forward(self):
        act_type = self.env.ref('openeducat_activity.op_activity_type_3')
        for record in self:
            for student in record.student_ids:
                activity_vals = {
                    'student_id': student.id,
                    'type_id': act_type.id,
                    'date': self.date,
                    'description': 'Migration From' +
                    record.level_from_id.name +
                    ' to ' + record.level_to_id.name
                }
                self.env['op.activity'].create(activity_vals)
                student_level = self.env['op.student.level'].search(
                    [('student_id', '=', student.id),
                     ('level_id', '=', record.level_from_id.id)])
                student_level.write({
                    'level_id': record.level_to_id.id,
                    'batch_id': record.batch_id.id})
                reg_id = self.env['op.subject.registration'].create({
                    'student_id': student.id,
                    'batch_id': record.batch_id.id,
                    'level_id': record.level_to_id.id,
                    'min_unit_load': record.level_to_id.min_unit_load or 0.0,
                    'max_unit_load': record.level_to_id.max_unit_load or 0.0,
                    'state': 'draft',
                })
                reg_id.get_subjects()
                if not record.optional_sub:
                    reg_id.action_submitted()
                    reg_id.action_approve()
