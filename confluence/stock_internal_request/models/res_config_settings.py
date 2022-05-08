# -*- coding: utf-8 -*-
##############################################################################
#
#    ZOO, zoo-business Solution
#    Copyright (C) 2017-2020 zoo (<http://www.zoo-business.com>).
#
##############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    location_id = fields.Many2one('stock.location', "Source Location", readonly=False,
                                       related='company_id.location_id')
    picking_type_id = fields.Many2one("stock.picking.type", string="Operation Type",readonly=False,
                                      related='company_id.picking_type_id')
