import statistics
from statistics import mode, mean

from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError

import time
from datetime import date, datetime
from odoo import models, api ,_
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
# from num2words import num2words
class TeachersStationaryUoiWizard(models.TransientModel):
    _name = 'teachers.stationary.uoi.wizard'
    _description = 'Teachers Stationary UOI Report'

    from_date = fields.Date('From', default=fields.Date.today())
    to_date = fields.Date('To', default=fields.Date.today())
    op_level_id = fields.Many2one('op.level', string="Level Name")
    op_class_id = fields.Many2one('op.classroom', string="class")
    def get_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'from_date': fields.Date.from_string(self.from_date),
                'to_date': fields.Date.from_string(self.to_date),
                'op_level_id': self.op_level_id.id,
                'op_level_name': self.op_level_id.name,
                'op_class_id': self.op_class_id.id,
                'op_class_id_name': self.op_class_id.name,

            },
        }

        return self.env.ref('stock_confluence.stationary_request_report').report_action(self, data=data)


class PriceAnalysisReport(models.AbstractModel):
    _name = 'report.stock_confluence.stationary_request_report_template'
    #
    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     payslips = self.env['hr.payslip.run'].browse(docids)
    #
    #     return {'docs': self.env['hr.payslip.run'].browse(docids),
    #             'fun': self._get_rule_total,
    #
    #             }

    @api.model
    def _get_report_values(self, docids, data=None):
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']

        op_level_id = data['form']['op_level_id']
        op_level_id_name = data['form']['op_level_name']
        op_class_id = data['form']['op_class_id']
        op_class_id_name = data['form']['op_class_id_name']
        product_r = []
        # product_id = self.env['product.product'].search([])
        move_id = self.env['stock.move'].search([]).filtered(lambda l: l.picking_id.picking_type_id.code == 'outgoing' and l.op_level_id.id == op_level_id and l.op_class_id.id == op_class_id and l.picking_id.is_requisition_out_transfer)
        if move_id:
            for rec in move_id:
                product_r.append({'product_name': rec.product_id.name ,'requested': rec.product_uom_qty,'give': rec.product_uom_qty})          # opening_balance = first_doc.balance

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'from_date': from_date,
            'to_date': to_date,
            'op_level_id_name': op_level_id_name,
            'op_class_id_name': op_class_id_name,
            'product_r': product_r,


        }
