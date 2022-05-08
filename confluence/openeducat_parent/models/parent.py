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


class OpParent(models.Model):
    _name = "op.parent"
    _description = "Parent"

    name = fields.Many2one('res.partner', 'Name', required=True)
    user_id = fields.Many2one('res.users', string='User', store=True)
    student_ids = fields.One2many('op.student','parent_id', string='Student(s)')
    mobile = fields.Char(string='Mobile')
    active = fields.Boolean(default=True)

    _sql_constraints = [(
        'unique_parent',
        'unique(name)',
        'Can not create parent multiple times.!'
    )]

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.user_id = self.name.user_id and self.name.user_id.id or False
            self.mobile = self.name.mobile

    @api.model
    def create(self, vals):
        res = super(OpParent, self).create(vals)
        if vals.get('student_ids', False) and res.name.user_id:
            student_ids = self.student_ids.browse(res.student_ids.ids)
            user_ids = [student_id.user_id.id for student_id in student_ids
                        if student_id.user_id]
            res.user_id.child_ids = [(6, 0, user_ids)]
        return res

    def write(self, vals):
        for rec in self:
            res = super(OpParent, self).write(vals)
            if vals.get('student_ids', False) and rec.name.user_id:
                student_ids = rec.student_ids.browse(rec.student_ids.ids)
                usr_ids = [student_id.user_id.id for student_id in student_ids
                           if student_id.user_id]
                rec.user_id.child_ids = [(6, 0, usr_ids)]
            rec.clear_caches()
            return res

    def unlink(self):
        for record in self:
            if record.name.user_id:
                record.user_id.child_ids = [(6, 0, [])]
            return super(OpParent, self).unlink()

    def create_parent_user(self):
        template = self.env.ref('openeducat_parent.parent_template_user')
        users_res = self.env['res.users']
        for record in self:
            if not record.name.email:
                raise exceptions.Warning(_('Update parent email id first.'))
            if not record.name.user_id:
                groups_id = template and template.groups_id or False
                user_ids = [
                    x.user_id.id for x in record.student_ids if x.user_id]
                user_id = users_res.create({
                    'name': record.name.name,
                    'partner_id': record.name.id,
                    'login': record.name.email,
                    'is_parent': True,
                    'tz': self._context.get('tz'),
                    'groups_id': groups_id,
                    'child_ids': [(6, 0, user_ids)]
                })
                record.user_id = user_id
                record.name.user_id = user_id


