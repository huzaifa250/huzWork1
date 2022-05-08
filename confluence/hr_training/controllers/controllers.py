# -*- coding: utf-8 -*-
# from odoo import http


# class HrTraining(http.Controller):
#     @http.route('/hr_training/hr_training/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_training/hr_training/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_training.listing', {
#             'root': '/hr_training/hr_training',
#             'objects': http.request.env['hr_training.hr_training'].search([]),
#         })

#     @http.route('/hr_training/hr_training/objects/<model("hr_training.hr_training"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_training.object', {
#             'object': obj
#         })
