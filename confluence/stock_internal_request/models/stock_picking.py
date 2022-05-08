# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    internal_requisition_id = fields.Many2one("internal.requisition", string="Internal Requisition", readonly=True)

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.move_ids_without_package:
            if self.internal_requisition_id:
                self.internal_requisition_id.write({'state': 'done'})
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    requisition_line_id = fields.Many2one('internal.requisition.line',
                                          'Requisition Order Line', ondelete='set null', index=True, readonly=True)
    internal_requisition_id = fields.Many2one("internal.requisition", string="Internal Requisition", readonly=True)
