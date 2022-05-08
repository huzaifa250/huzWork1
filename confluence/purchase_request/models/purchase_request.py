# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, time
from odoo.tools.float_utils import float_compare
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

from dateutil.relativedelta import relativedelta


import datetime


_STATES = [
    ("draft", "Draft"),
    ("to_approve", "To be approved"),
    ("approved", "Approved"),
    ("confirm", "Confirm"),
    ("po_create", "Purchase Requisition Created"),
    ('to_delivery_order','Delivery Order'),
    ('coordinetar_approval','Wait Coordinetar Approval'),
    ('purchase_officer_approval','Wait Purchase Officer Approval'),
    ("rejected", "Rejected"),
    ("done", "Done"),
]


# class PurchaseOrder(models.Model):
#
#     _inherit = "purchase.order"
#
#
#     purchase_order_conflu_id = fields.Many2one('purchase.order.conflu', string='Purchase Confluence ID')
#     is_order_confluence = fields.Boolean("Is Purchase Order Confluence",default=False)
#     date_order = fields.Datetime('Order Deadline', required=False, states=READONLY_STATES, index=True, copy=False, default=fields.Datetime.now,


class PurchaseRequisition(models.Model):

    _inherit = "purchase.requisition"

    purchase_request_id = fields.Many2one("purchase.request")
    is_request = fields.Boolean("Is Request")
    op_level_id = fields.Many2one('op.level', string='Level')
    op_class_id = fields.Many2one('op.classroom', string='Class Room', domain="[('level_id','=',op_level_id)]")




class PurchaseOrderConflu(models.Model):

    _name = "purchase.order.conflu"
    _description = "Purchase Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "sequence"
    # _order = "id desc"

    @api.model
    def _get_default_employee(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)],limit=1)
        return employee_id.id

    @api.model
    def _company_get(self):
        return self.env["res.company"].browse(self.env.company.id)

    name = fields.Char("Request")
    employee_id = fields.Many2one("hr.employee",default=_get_default_employee)
    department_id = fields.Many2one(related='employee_id.department_id', string='Department')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase ID',default=False)
    description = fields.Text("Description")
    state = fields.Selection([("draft", "Draft"),("confirm", "Confirm"), ("done", "Done")], string="State",
                             default="draft")
    purchase_count = fields.Integer(string='Purchase', compute='_compute_purchase_ids')
    sequence = fields.Char(string='Sequence',readonly=True,rack_visibility='onchange', index=True, default=lambda self: _( 'NEW' ))

    # company_id = fields.Many2one(comodel_name="res.company", string="Company",required=True, default=_company_get,track_visibility="onchange", states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})

    # create sequence
    @api.model
    def create(self, vals):
        result = super(PurchaseOrderConflu, self).create(vals)
        # month = datetime.strptime(result.date(field), '%Y-%m-%d').strftime('%m')
        if vals.get('sequence', 'New') == 'New':
            result.sequence = self.env['ir.sequence'].next_by_code('purchase.order.conflu') or 'New'

        return result

    def action_confirm(self):
        """
        A method to confirm services
        """
        self.write({'state': 'confirm'})

    def action_done(self):
        """
        A method to done services
        """
        self.write({'state': 'done'})

    def set_to_draft(self):
        """
        A method to draft services
        """
        self.write({'state': 'draft'})
        # self.write({'state': 'new'})

    def create_purchase_order(self):
        purchase_obj = self.env['purchase.order']
        lines = []
        for rec in self:
            purchase_id = purchase_obj.create({
                                                'purchase_order_conflu_id': rec.id,
                                                'origin': rec.sequence,
                                                'employee_id': rec.employee_id.id,
                                                # 'company_id': rec.company_id.id,
                                                # 'description': rec.description,
                                                'is_order_confluence': True,
                                            })

            rec.purchase_order_id = purchase_id
        self.write({'state': 'done'})

    def _compute_purchase_ids(self):
        for rec in self:
            purchase_ids = self.env['purchase.order'].search([('purchase_order_conflu_id', '=', rec.id)])
            rec.purchase_count = len(purchase_ids)

    def get_purchase_order_formview(self):
        if self.purchase_count > 0:
            view = self.env.ref('purchase.purchase_order_kpis_tree')
            # view = self.env.ref('account.view_in_invoice_bill_tree')
            form_view = self.env.ref('purchase.purchase_order_form')
            return {
                'name': _('Purchase Order'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'purchase.order',
                'domain': [('purchase_order_conflu_id', '=', self.id)],
                'views': [(view.id, 'tree'),(form_view.id, 'form')],

            }



class PurchaseRequest(models.Model):

    _name = "purchase.request"
    _description = "Purchase Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _rec_name = "sequence"

    @api.model
    def _company_get(self):
        return self.env["res.company"].browse(self.env.company.id)

    @api.model
    def _get_default_requested_by(self):
        return self.env["res.users"].browse(self.env.uid)


    @api.model
    def create(self, vals):
        res = super(PurchaseRequest, self).create(vals)
        next_seq = self.env['ir.sequence'].get('purchase.request')
        res.update({'name': next_seq})
        return res


    name = fields.Char( string="Request Reference",readonly="1",track_visibility="onchange", states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    vendor_id = fields.Many2one( comodel_name="res.partner", string="Vendor", required=False,states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    origin = fields.Char(string="Source Document",states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    date_start = fields.Date(string="Request date", help="Date when the user initiated the request.",default=fields.Date.context_today,track_visibility="onchange" , states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    requested_by = fields.Many2one( comodel_name="res.users", string="Requested by", required=True, copy=False, track_visibility="onchange",default=_get_default_requested_by, index=True, states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    request_type = fields.Selection([('local', 'Local Request'),('international', 'International Request')], string='Request Type', required=True,default='local', states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    description = fields.Text(string="Description", states={'done': [('readonly', True)]})
    company_id = fields.Many2one(comodel_name="res.company", string="Company",required=True, default=_company_get,track_visibility="onchange", states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    line_ids = fields.One2many( comodel_name="purchase.request.line",inverse_name="request_id", string="Products to Purchase", readonly=False, copy=True,track_visibility="onchange", states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    state = fields.Selection(selection=_STATES, string="Status", index=True, track_visibility="onchange", required=True,copy=False, default="draft", states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    purchase_count = fields.Integer(string="Purchases count",compute='_compute_purchase_count' ,readonly=True,states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
     # purchase_type = fields.Selection([('spare', 'Spare Parts'),('vehicle', 'Vehicle'),('other', 'Others')],string='Purchase Type',required=True,Tracking =True,states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    op_level_id = fields.Many2one('op.level', string='Level')
    op_class_id = fields.Many2one('op.classroom', string='Class Room', domain="[('level_id','=',op_level_id)]")
    warehouse_id = fields.Many2one('stock.warehouse', "Warehouse",tracking=True ,required=True)
    picking_type_id = fields.Many2one("stock.picking.type", string="Operation Type", tracking=True,
                                      related='warehouse_id.out_type_id')
    location_dest_id = fields.Many2one('stock.location', compute='compute_location_dest', string="Destination Location", required=False,tracking=True, store=True)
    stock_picking_id = fields.Many2one('stock.picking', string="Stock Picking ID",tracking=True)
    purchase_requisition_id = fields.Many2one('purchase.requisition', "Purchase Requisition ID",tracking=True)
    stock_delivery_count = fields.Integer(string='Delivery', compute='_compute_stock_move_ids')
    sequence = fields.Char(string='Sequence', readonly=True, rack_visibility='onchange', index=True,default=lambda self: _('NEW'))
    is_purchase_request = fields.Boolean('IS Purchase Request',default=False)
    requisition_responsible = fields.Many2one("res.users", string="Requisition Responsible",
                                              default=lambda self: self.env.user, required=False)

    group_id = fields.Many2one('procurement.group', string="Procurement Group", copy=False)

    # create sequence
    @api.model
    def create(self, vals):
        result = super(PurchaseRequest, self).create(vals)
        # month = datetime.strptime(result.date(field), '%Y-%m-%d').strftime('%m')
        if vals.get('sequence', 'New') == 'New':
            result.sequence = self.env['ir.sequence'].next_by_code('purchase.request') or 'New'

        return result


    def get_stock_move_treeview(self):
        if self.stock_delivery_count > 0:
            view = self.env.ref('stock.vpicktree')
            form_view = self.env.ref('stock.view_picking_form')
            return {
                'name': _('Transfers'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'stock.picking',
                'domain': [('requisition_out_id', '=', self.id)],
                'views': [(view.id, 'tree'), (form_view.id, 'form')],

            }
    @api.depends('warehouse_id')
    def compute_location_dest(self):
        for order in self:
            order.location_dest_id = self.env['stock.location'].search([('warehouse_id', '=', order.warehouse_id.id), ('usage', '=', 'customer')])

    def _compute_stock_move_ids(self):
        for rec in self:
            stock_move_ids = self.env['stock.picking'].search([('requisition_out_id', '=', rec.id)])
            rec.stock_delivery_count = len(stock_move_ids)



    def _compute_purchase_count(self):
        for rec in self:
            orders = self.env['purchase.requisition'].search([('purchase_request_id','=',rec.id)])
            rec.purchase_count = len(orders)


    def unlink(self):
        for request in self:
            if request.state != 'draft':
                raise UserError(
                    _("You cannot delete a purchase request which is not draft.")
                )
        return super(PurchaseRequest, self).unlink()

    def button_draft(self):
        return self.write({"state": "draft"})

    def button_to_approve(self):
        if not self.line_ids:
            raise UserError(
                _(
                    "You can't request an approval for a purchase request "
                    "which is empty. (%s)"
                )
                % self.name
            )
        if self.request_type == 'local':
            self.write({"state": "coordinetar_approval"})
        if self.request_type == 'international':
            self.write({"state": "approved"})

    # def button_approved(self):
    #     return self.write({"state": "approved"})

    def button_rejected(self):
        return self.write({"state": "rejected"})

    def button_confirm_done(self):
        return self.write({"state": "purchase_officer_approval"})

    def button_done(self):
        return self.write({"state": "done"})

    # @api.model
    # def _prepare_picking(self):
    #     return {
    #         'picking_type_id': self.warehouse_id.out_type_id.id,
    #         # 'partner_id': self.requisition_responsible.partner_id.id,#close to brevent update End User in serial
    #         'scheduled_date': datetime.today() + relativedelta(hour=int(self.request_type_id.response_hours)),
    #         'origin': self.sequence,
    #         'requisition_out_id': self.id,
    #         'location_dest_id': self.location_dest_id.id,
    #         'location_id': self.warehouse_id.lot_stock_id.id,
    #         'company_id': self.company_id.id,
    #         # 'note': self.reason_requisition,
    #     }

    def create_requisition(self):
        moves = []
        purchase_moves = []
        for line in self.line_ids:
            sub = line.product_qty - line.qty_available
            # if sub <= line.product_qty:
            sub = line.product_qty - line.qty_available
            if sub <= 0 or sub < line.qty_available:
                vals = (0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_id.id,

                    'product_uom_qty': line.product_qty,
                    'name': line.product_id.name,
                    'location_id': self.warehouse_id.lot_stock_id.id,
                    'location_dest_id': self.warehouse_id.lot_stock_id.id,
                })
                moves.append(vals)
            if sub > 0 or sub > line.qty_available:
                vals = (0, 0,{
                                'product_id': line.product_id.id,
                                'product_qty': line.sub,
                                'product_description_variants': line.name,
                                'product_uom_id': line.product_id.uom_po_id.id,
                            })
                purchase_moves.append(vals)


        if moves:
            for order in self:
                # order.write({'approve_line_ids': False})
                pickings = order.stock_picking_id.filtered(lambda x: x.state not in ('received', 'cancel'))
                if not pickings:
                    if not self.group_id:
                        self.group_id = self.group_id.create({
                            'name': self.sequence,
                            'partner_id': self.requisition_responsible.partner_id.id,
                        })
                    # location_dest_stock_id = self.env['stock.location'].search([('warehouse_id', '=', order.warehouse_id.id),('usage', '=', 'customer')],limit=1).id
                    # location_dest_purchase_id = self.env['stock.location'].search([('warehouse_id', '=', order.warehouse_id.id),('usage', '=', 'supplier')],limit=1).id
                    print('\n')
                    print('\n')
                    # print('------------------',location_dest_stock_id)
                    picking = order.env['stock.picking'].create({'user_id': order.env.uid,
                                                                 'requisition_out_id': order.id,
                                                                 'partner_id': order.vendor_id.id,
                                                                 'picking_type_id': order.warehouse_id.out_type_id.id,
                                                                 'location_id': order.warehouse_id.lot_stock_id.id,
                                                                 'location_dest_id': order.location_dest_id.id,
                                                                 'origin': order.sequence,
                                                                 # 'move_ids_without_package': moves,
                                                                 # 'move_lines': moves,
                                                                 'op_level_id': order.op_level_id.id,
                                                                 'op_class_id': order.op_class_id.id,
                                                                 'is_requisition_out_transfer': True,
                                                                  })
                    order.stock_picking_id = picking
                else:

                    picking = pickings[0]
                moves = order.line_ids.filtered(lambda x: x.product_qty - x.qty_available <= 0 or x.product_qty - x.qty_available < x.qty_available)._create_stock_moves(picking)
                # To Reserve just entered lot_id
                if order.request_type == 'local':
                    for move in moves:
                        for line in move.move_line_ids:
                            product_qty = move.product_uom._compute_quantity(
                                1, move.product_id.uom_id, rounding_method='HALF-UP')
                            available_quantity = order.env['stock.quant']._get_available_quantity(
                                move.product_id,
                                move.location_id,
                                lot_id=line.lot_id,
                                strict=False,
                            )
                            move._update_reserved_quantity(
                                product_qty,
                                available_quantity,
                                move.location_id,
                                lot_id=line.lot_id,
                                strict=False,
                            )

                moves = moves.filtered(lambda x: x.state not in ('received', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'requisition_line_id': order},
                                               subtype_id=self.env.ref('mail.mt_note').id)

            picking.action_assign()
            self.write({'state': 'done'})


        if purchase_moves:
            purchase_requisition = self.env['purchase.requisition'].create({
                                                'user_id': self.env.uid,
                                                'ordering_date': self.date_start,
                                                # 'vendor_id': self.vendor_id.id,
                                                'origin': self.sequence,
                                                'purchase_request_id': self.id,
                                                'line_ids': purchase_moves,
                                                'op_level_id': self.op_level_id.id,
                                                'op_class_id': self.op_class_id.id,
                                                'is_request': True,
                                                'state': 'draft',
                                              })

            self.purchase_requisition_id = purchase_requisition
            self.write({'state': 'done'})

class PurchaseRequestLine(models.Model):

    _name = "purchase.request.line"
    _description = "Purchase Request Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Description",required=True, track_visibility="onchange",tracking=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Product",track_visibility="onchange")
    qty_available = fields.Float(related="product_id.qty_available",string="Quantity On Hand",tracking=True )
    price_unit = fields.Float('Price Unit',tracking=True)
    product_qty = fields.Float( string="Requested Quantity", track_visibility="onchange", digits="Product Unit of Measure")
    product_uom = fields.Many2one(related='product_id.uom_id', string="UoM")
    # product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    request_id = fields.Many2one(comodel_name="purchase.request", string="Purchase Request",ondelete="cascade",  readonly=True, index=True)
    company_id = fields.Many2one(comodel_name="res.company",related="request_id.company_id", string="Company", store=True )
    requested_by = fields.Many2one(comodel_name="res.users",related="request_id.requested_by",string="Requested by",store=True)
    requested = fields.Float('Requested')
    move_ids = fields.One2many('stock.move', 'requisition_line_id_rr', string='Reservation', readonly=True, copy=False)
    qty_received = fields.Float("Received Qty", compute='compute_qty_delivery',
                                compute_sudo=True, store=True, digits='Product Unit of Measure')
    op_level_id = fields.Many2one('op.level', string='Level',compute='compute_level_class_id',store=True)
    op_class_id = fields.Many2one('op.classroom', string='Class Room',compute='compute_level_class_id',store=True)

    @api.onchange('product_id')
    def product_description_onchange(self):
        for rec in self:
            rec.name = rec.product_id.name


    @api.depends('request_id.op_level_id','request_id.op_class_id')
    def compute_level_class_id(self):
        self.op_level_id = False
        self.op_class_id = False
        for rec in self:
            rec.op_level_id = rec.request_id.op_level_id.id
            rec.op_class_id = rec.request_id.op_class_id.id




    @api.depends('move_ids.state')
    def compute_qty_delivery(self):
        for order in self:
            qty = 0.0
            for move in order.move_ids:
                if move.state == 'done' and move.location_dest_id == order.request_id.location_dest_id:
                    qty += move.product_uom_qty
            order.qty_received = qty
    # @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        for move in self.move_ids.filtered(
                lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "internal"):
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            'name': self.name or '',
            'product_id': self.product_id.id,
            'description_picking': self.name,
            'product_uom': self.product_uom.id,
            'date': fields.date.today(),
            'location_id': self.request_id.warehouse_id.lot_stock_id.id,
            'location_dest_id': self.request_id.location_dest_id.id,
            'picking_id': picking.id,
            'partner_id': self.request_id.requisition_responsible.partner_id.id,
            'state': 'draft',
            'product_uom_qty': qty,
            'requisition_line_id_rr': self.id,
            'company_id': self.request_id.company_id.id,
            'picking_type_id': self.request_id.warehouse_id.out_type_id.id,
            'group_id': self.request_id.group_id.id,
            'op_level_id': self.op_level_id.id,
            'op_class_id': self.op_class_id.id,
            'purchase_request_line_id_rr': self.request_id.id,
            'route_ids': self.request_id.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in self.request_id.picking_type_id.warehouse_id.route_ids])] or [],
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if self.product_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = diff_quantity
            res.append(template)
        return res

    # @api.multi
    def _create_stock_moves(self, picking):
        values = []
        for line in self:
            for val in line._prepare_stock_moves(picking):
                values.append(val)
            picking.move_line_ids.write({'op_class_id': line.op_class_id.id})
        return self.env['stock.move'].create(values)

    def _update_received_qty(self):
        for line in self:
            total = 0.0
            for move in line.move_ids:
                if move.state == 'done':
                    if move.location_dest_id.usage == "internal":
                        if move.to_refund:
                            total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                    else:
                        total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
            line.qty_received = total

class StockPicking(models.Model):
    _inherit = "stock.picking"

    requisition_out_id = fields.Many2one('purchase.request')
    is_picking_out_transfer = fields.Boolean('is transfer')
    op_level_id = fields.Many2one('op.level', string='Level')
    op_class_id = fields.Many2one('op.classroom', string='Class Room', domain="[('level_id','=',op_level_id)]")
    is_requisition_out_transfer = fields.Boolean('is requisition out transfer',default=False)


    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.product_uom = self.product_id.uom_id.id

    def _merge_in_existing_line(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        """ This function purpose is to be override with the purpose to forbide _run_buy  method
        to merge a new po line in an existing one.
        """
        return True
# def button_validate(self):
    #     res = super(Stockpicking, self).button_validate()
    #     purchase_reques_ids = self.env['purchase.reques'].search([('id', '=', self.requisition_out_id)])
    #     for rec in purchase_reques_ids:
    #         rec. = self.quantity_done


        # print('------------------')
#
class StockMove(models.Model):
    _inherit = "stock.move"
    _description = "Stock confluence"

    requisition_line_id_rr = fields.Many2one('purchase.request.line',string='request')
    purchase_request_line_id_rr = fields.Many2one('purchase.request',string='request')
    op_level_id = fields.Many2one('op.level', string='Level')
    op_class_id = fields.Many2one('op.classroom', string='Class Room')

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        vals = {
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'location_id': self.location_id.id,
            'op_level_id': self.op_level_id.id,
            'op_class_id': self.op_class_id.id,
            'picking_id': self.picking_id.id,
            'company_id': self.company_id.id,
        }
        if quantity:
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom, rounding_method='HALF-UP')
            uom_quantity = float_round(uom_quantity, precision_digits=rounding)
            uom_quantity_back_to_product_uom = self.product_uom._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
            if float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                vals = dict(vals, product_uom_qty=uom_quantity)
            else:
                vals = dict(vals, product_uom_qty=quantity, product_uom_id=self.product_id.uom_id.id)
        package = None
        if reserved_quant:
            package = reserved_quant.package_id
            vals = dict(
                vals,
                location_id=reserved_quant.location_id.id,
                lot_id=reserved_quant.lot_id.id or False,
                package_id=package.id or False,
                owner_id =reserved_quant.owner_id.id or False,
            )
        # apply putaway
        location_dest_id = self.location_dest_id._get_putaway_strategy(self.product_id, quantity=quantity or 0, package=package, packaging=self.product_packaging_id).id
        vals['location_dest_id'] = location_dest_id
        return vals


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    _description = "Stock confluence"

    purchase_request_line_id = fields.Many2one('purchase.request.line',string='request')
    op_level_id = fields.Many2one('op.level', string='Level')
    op_class_id = fields.Many2one('op.classroom', string='Class Room')

