# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class InternalRequisition(models.Model):
    _name = 'internal.requisition'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one("hr.employee", string="Employee", required=False, tracking=True)
    department_id = fields.Many2one("hr.department", string="department", related='employee_id.department_id',
                                    readonly=False, store=True)
    company_id = fields.Many2one("res.company", string="Company", related='requisition_responsible.company_id')
    requisition_responsible = fields.Many2one("res.users", string="Requisition Responsible",
                                              default=lambda self: self.env.user, required=False)
    requisition_date = fields.Date(string="Requisition Date", required=True, tracking=True,
                                   default=lambda self: fields.Date.today())
    origin = fields.Char(string="Source Document", required=False,compute='_compute_origin', store=True)
    received_date = fields.Date(string="Received Date", required=False, tracking=True)
    requisition_deadline = fields.Date(string="Requisition Deadline", required=False)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', tracking=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    reason_requisition = fields.Text('Reason Requisition', tracking=True)
    requisition_line_ids = fields.One2many("internal.requisition.line", "requisition_id", string='Requisition Lines',
                                           copy=True)
    location_id = fields.Many2one('stock.location', "Source Location", required=False, tracking=True,
                                  related='warehouse_id.out_type_id.default_location_src_id')
    location_dest_id = fields.Many2one('stock.location', "Destination Location", required=False,
                                       tracking=True)
    picking_id = fields.Many2one("stock.picking", string="Internal Picking", readonly=True, tracking=True,
                                 copy=False)
    picking_type_id = fields.Many2one("stock.picking.type", string="Operation Type", tracking=True,
                                      related='warehouse_id.out_type_id')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('waiting_dept_app', 'Waiting Department Approval'),
                                        ('waiting_app', 'Waiting Approval'),
                                        ('approved', 'Approved'),
                                        ('requested_stock', 'Waiting To Delivery'),
                                        ('reject', 'Reject'),
                                        ('partial_delivered', 'Partial Delivered'),
                                        ('done', 'Done'),
                                        ('cancel', 'Cancelled'), ],
                             string="State", default='draft', tracking=True, readonly=True)
    confirmed_by = fields.Many2one("res.users", string="Confirmed By", tracking=True, readonly=True)
    confirmed_date = fields.Date("Confirmed Date", tracking=True, readonly=True)
    department_manager = fields.Many2one("res.users", string="Department Approved By", tracking=True,
                                         readonly=True)
    request_app_by = fields.Many2one("res.users", string="Approved By", tracking=True, readonly=True)
    reject_by = fields.Many2one("res.users", string="Reject By", tracking=True, readonly=True)
    dept_app_date = fields.Date(string="Department Approval Date", tracking=True, readonly=True)
    app_date = fields.Date(string="Approved Date", tracking=True, readonly=True)
    reject_date = fields.Date(string="Reject Date", tracking=True, readonly=True)
    internal_req_count = fields.Integer(string="Internal Requisition", compute='_compute_picking_ids')
    request_count = fields.Integer(string="Purchase Request", compute='_compute_purchase_request')
    group_id = fields.Many2one('procurement.group', string="Procurement Group", copy=False)
    request_type_id = fields.Many2one("request.type", string="Request Type", ondelete='restrict')
    delivery_state = fields.Char(compute='compute_state')
    vendor_id = fields.Many2one( comodel_name="res.partner", string="Vendor",)
    purchase_type = fields.Selection([('spare', 'Spare Parts'),('vehicle', 'Vehicle'),('other', 'Others')],string='Purchase Type',required=True,Tracking =True,states={'done': [('readonly', True)],'rejected': [('readonly', True)],'po_create': [('readonly', True)]})
    picking_ids = fields.One2many('stock.picking', 'internal_requisition_id', string='Pickings', copy=False)
    request = fields.Boolean('request')
    is_created = fields.Boolean('Created')

    @api.onchange('department_id')
    def onchange_department_id(self):
        if self.department_id:
            self.location_dest_id = self.department_id.location_dest_id.id

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.internal_req_count = len(order.picking_ids)

    def _compute_origin(self):
        for rec in self:
            rec.origin = rec.self.id
    def _compute_purchase_request(self):
        request_ids = self.env['purchase.request'].search(
            [('internal_request_id', '=', self.id)])
        for order in self:
            order.request_count = len(request_ids)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.requisition') or 'New'
            result = super(InternalRequisition, self).create(vals)
            return result

    @api.depends('picking_id.state')
    def compute_state(self):
        for order in self.picking_id:
            if order.state == 'done':
                self.write({'state': 'done'})
            elif order.state == 'confirmed':
                self.write({'state': 'partial_delivered'})
            elif order.state == 'cancel':
                self.write({'state': 'cancel'})
            else:
                self.write({'state': 'draft'})

    # @api.multi
    def action_approve(self):
        for order in self:
            order.write({'request_app_by': self.env.user.id,
                         'app_date': fields.Date.today(),
                         'state': 'approved'})

    # @api.multi
    def action_requested_stock(self):
        self._create_picking()
        self.write({'state': 'requested_stock'})

    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.requisition_responsible.partner_id.id,
            })
        if not self.location_dest_id.id:
            raise UserError(_("You must set a Department Location for this Department %s") % self.department_id.name)
        return {
            'picking_type_id': self.warehouse_id.out_type_id.id,
            'partner_id': self.requisition_responsible.partner_id.id,
            'date': self.requisition_date,
            'origin': self.name,
            'internal_requisition_id': self.id,
            'location_dest_id': self.location_dest_id.id,
            'location_id': self.warehouse_id.out_type_id.default_location_src_id.id,
            'company_id': self.company_id.id,
        }

    # @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.requisition_line_ids.mapped('product_id.type')]):
                pickings = order.picking_id.filtered(lambda x: x.state not in ('received', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                    order.picking_id = picking.id
                else:
                    picking = pickings[0]
                moves = order.requisition_line_ids._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('received', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                if order.picking_id.state == 'confirmed':
                    order.request = True
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'internal_requisition_id': order},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return True

    # @api.multi
    # def action_received(self):
    #     return self.write({'state': 'received'})

    # @api.multi
    def action_reject(self):
        for order in self:
            order.write({'reject_by': self.env.user.id,
                         'reject_date': fields.Date.today(),
                         'state': 'reject'})

    # @api.multi
    def action_cancel(self):
        for order in self:
            for move in order.requisition_line_ids.mapped('move_ids'):
                if move.state == 'done':
                    raise UserError(
                        _('Unable to cancel request order %s as some receptions have already been done.') % (
                            order.name))
            # If the product is MTO, change the procure_method of the the closest move to purchase to MTS.
            # The purpose is to link the po that the user will manually generate to the existing moves's chain.
            if order.state in ('draft','waiting_dept_app', 'waiting_app', 'approved'):
                for order_line in order.requisition_line_ids:
                    order_line.move_ids._action_cancel()
            for pick in order.picking_ids.filtered(lambda r: r.state != 'cancel'):
                pick.action_cancel()
        return self.write({'state': 'cancel'})

    # @api.multi
    def action_submit(self):
        for order in self:
            if not order.requisition_line_ids:
                raise UserError(_('You can not submit the requisition without fill lines'))
            order.write({'confirmed_by': self.env.user.id,
                         'confirmed_date': fields.Date.today(),
                         'state': 'waiting_dept_app'})

    # @api.multi
    def action_dept_approve(self):
        for order in self:
            order.write({'department_manager': self.env.user.id,
                         'dept_app_date': fields.Date.today(),
                         'state': 'waiting_app'})

    # @api.multi
    def action_set_to_draft(self):
        self.write({'state': 'draft'})

    # @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You can not delete no draft record!"))
        return super(InternalRequisition, self).unlink()

    # @api.multi
    def action_internal_requisition(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    def _prepare_request(self):
        return {
            'requested_by': self.env.uid,
            'date_start': self.requisition_date,
            'vendor_id': self.vendor_id.id,
            'internal_request_id': self.id,
            'purchase_type': self.purchase_type,
            'description': self.reason_requisition,
            'is_internal_request': True,
            'request_type': 'local',
            'state': 'draft',
        }

    def create_purchase_request(self):
        request_obj = self.env['purchase.request']
        res = self._prepare_request()
        request = request_obj.create(res)

        for res in self:
            for rec in res.requisition_line_ids:
                res.env['purchase.request.line'].create({'request_id': request.id,
                                                        'product_id': rec.product_id.id,
                                                        'name': rec.name,
                                                        'product_qty': rec.product_qty,
                                                        'product_uom_id': rec.product_id.uom_po_id.id,
                                                       })
            self.write({'is_created': True})



class InternalRequisitionLine(models.Model):
    _name = 'internal.requisition.line'

    requisition_id = fields.Many2one("internal.requisition", string="Requisition")
    product_id = fields.Many2one('product.product', string='Product', required=True,
                                 domain=[('type', 'in', ['product', 'consu'])])
    name = fields.Text(string='Description', required=True)
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                               default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    move_ids = fields.One2many('stock.move', 'requisition_line_id', string='Reservation', readonly=True,
                               ondelete='set null', copy=False)


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
            'product_uom': self.product_uom.id,
            'date': self.requisition_id.requisition_date,
            'location_id': self.requisition_id.location_id.id,
            'location_dest_id': self.requisition_id.location_dest_id.id,
            'picking_id': picking.id,
            'partner_id': self.requisition_id.requisition_responsible.partner_id.id,
            'state': 'draft',
            'requisition_line_id': self.id,
            'company_id': self.requisition_id.company_id.id,
            'picking_type_id': self.requisition_id.picking_type_id.id,
            'group_id': self.requisition_id.group_id.id,
            'internal_requisition_id': self.requisition_id.id,
            'route_ids': self.requisition_id.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in self.requisition_id.picking_type_id.warehouse_id.route_ids])] or [],
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

    # def _prepare_product_bundle(self, picking):
    #     values = []
    #     if self.product_id.pack_ids:
    #         for item in self.product_id.pack_ids:
    #             values.append({
    #                 'name': item.product_id.name,
    #                 'origin': self.requisition_id.name,
    #                 'product_id': item.product_id.id,
    #                 'product_uom_qty': item.qty_uom * abs(self.product_qty),
    #                 'product_uom': item.uom_id and item.uom_id.id,
    #                 'date': self.requisition_id.requisition_date,
    #                 'location_id': self.requisition_id.location_id.id,
    #                 'location_dest_id': self.requisition_id.location_dest_id.id,
    #                 'picking_id': picking.id,
    #                 'partner_id': self.requisition_id.requisition_responsible.partner_id.id,
    #                 'state': 'draft',
    #                 'requisition_line_id': self.id,
    #                 'company_id': self.requisition_id.company_id.id,
    #                 'picking_type_id': self.requisition_id.picking_type_id.id,
    #                 'group_id': self.requisition_id.group_id.id,
    #                 'requisition_id': self.requisition_id.id,
    #                 'route_ids': self.requisition_id.picking_type_id.warehouse_id and [
    #             (6, 0, [x.id for x in self.requisition_id.picking_type_id.warehouse_id.route_ids])] or [],
    #             })
    #         return values

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


class RequestType(models.Model):
    _name = 'request.type'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    location_id = fields.Many2one('stock.location', "Location", required=False)
