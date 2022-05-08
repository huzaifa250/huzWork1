# -*- coding: utf-8 -*-
# from odoo import http


# class HrTariningPlan(http.Controller):
#     @http.route('/hr_training_plan/hr_training_plan/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_training_plan/hr_training_plan/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_training_plan.listing', {
#             'root': '/hr_training_plan/hr_training_plan',
#             'objects': http.request.env['hr_training_plan.hr_training_plan'].search([]),
#         })

#     @http.route('/hr_training_plan/hr_training_plan/objects/<model("hr_training_plan.hr_training_plan"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_training_plan.object', {
#             'object': obj
#         })
