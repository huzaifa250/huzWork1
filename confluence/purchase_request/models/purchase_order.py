# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models
from odoo.exceptions import UserError



class StockMove(models.Model):
    _inherit = "stock.move"
    purchase_request_line_id = fields.Many2one('purchase.request.line')

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_request_id = fields.Many2one('purchase.request', string="Purchase Request Ref",track_visibility="onchange")
    is_request_requisition = fields.Boolean('Requisition')
    purchase_order_conflu_id = fields.Many2one('purchase.order.conflu', string='Purchase Confluence ID')
    is_order_confluence = fields.Boolean("Is Purchase Order Confluence", default=False)
    date_order = fields.Datetime('Order Deadline', required=False, index=True, copy=False,
                                 default=fields.Datetime.now,help="Depicts the date within which the Quotation should be confirmed and converted into a purchase order.")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=False, change_default=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    company_id = fields.Many2one('res.company', 'Company', required=False, index=True, default=lambda self: self.env.company.id)
    employee_id = fields.Many2one("hr.employee")



