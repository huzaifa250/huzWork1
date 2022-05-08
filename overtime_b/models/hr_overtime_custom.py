from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class HrOverTimeCustom(models.Model):
    _inherit = 'hr.overtime'

    name = fields.Many2one('hr.employee', domain=[('contract_id.state', '=', 'open')], required=True)
    state = fields.Selection(selection_add=[('draft', 'Requester'), ('sent', 'Human Resources'),
                                            ('approve', 'Finance'),
                                            ('done', 'Done')], default='draft')
    overtime_date = fields.Date(string='Current Date', default=datetime.today())

    @api.constrains('is_working_day', 'is_holiday', 'is_eid_day', 'employee_id')
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
            # if rec.employee_id.contract_id.state != 'open':
            #     raise ValidationError(_("Employee must have running contract !"))
