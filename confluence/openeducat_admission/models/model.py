
from odoo import models, fields, api, _


class Assessment(models.Model):
    _name = "assessment.result"
    _rec_name = "subject_id"

    subject_id = fields.Many2one('op.subject',string="Subject Name")
    result = fields.Selection(selection=[('pass','Pass'),('fail','Fail')])
    assessment_paper = fields.Binary()
    admission_id = fields.Many2one('op.admission')



class School(models.Model):
    _name = "previous.school.result"
    _rec_name = "school_name"

    school_name = fields.Char(size=256)
    class_ids = fields.Many2many('op.level',string="Grades")
    admission_id = fields.Many2one('op.admission')
