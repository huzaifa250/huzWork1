# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#    Copyright (C) 2018-TODAY Tech-Receptives(<http://www.iatl-sd.com>).
#
###############################################################################

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    location_id = fields.Many2one('stock.location', string="Source Location")
    picking_type_id = fields.Many2one("stock.picking.type", string="Operation Type")