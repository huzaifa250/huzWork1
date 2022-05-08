
from odoo import models, fields, api, _


class InvoicesLine(models.Model):
    _inherit = 'account.move.line'

    student_id = fields.Many2one('op.student',related='move_id.student_id',store=True)
    level_id = fields.Many2one('op.level',string="Grade",related='move_id.admission_id.level_id',store=True)
    ledger_discount = fields.Float('Discount',compute='_compute_ledger_discount',store=True)

    @api.depends('move_id')
    def _compute_ledger_discount(self):
        for rec in self:
            discount = 0
            for line in rec.move_id.invoice_line_ids:
                if line.discount > 0:
                    discount = (line.price_unit * line.discount)/100
            rec.ledger_discount = discount                    
