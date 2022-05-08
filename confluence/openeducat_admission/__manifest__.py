# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenEduCat Inc
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<http://www.openeducat.org>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "OpenEduCat Admission",
    'version': '15.0.1.0',
    'license': 'LGPL-3',
    'category': 'Education',
    'sequence': 3,
    'summary': "Manage Admissions""",
    'complexity': "easy",
    'author': 'OpenEduCat Inc',
    'website': 'http://www.openeducat.org',
    'depends': [
        'openeducat_core','account','openeducat_parent'
        # 'openeducat_fees'
    ],
    'data': [
        'data/payment_cron.xml',
        'security/ir.model.access.csv',
        'data/admission_sequence.xml',
        'views/admission_register_view.xml',
        'views/pre_application_view.xml',
        'views/registration_form_view.xml',
        'report/report_admission_analysis.xml',
        'report/admission_form_template.xml',
        'report/registration_form_template.xml',
        'report/re_registration_form_template.xml',
        'report/report_menu.xml',
        'wizard/admission_analysis_wizard_view.xml',
         'views/re_registration_view.xml',
        'menus/op_menu.xml',
        'views/student_fees_view.xml',
       
    ],
    'demo': [
        # 'demo/admission_register_demo.xml',
        # 'demo/admission_demo.xml',
    ],
    'test': [],
    'images': [
        'static/description/openeducat_admission_banner.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
