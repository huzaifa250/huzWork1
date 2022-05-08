# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Contract confluence',
    'version': '1.1',
    'category': 'Human Resources/Employees',
    'sequence': 100,
    'summary': 'Centralize employee information',
    'description': "",
    'website': 'https://www.odoo.com/app/employees',
    'depends': [
        'hr',
        'hr_contract',
        'hr_employee_confluence'
    ],
    'data': [
        # 'security/hr_security.xml',
        'security/ir.model.access.csv',
        'views/hr_contract.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'mail.assets_discuss_public': [
            'hr/static/src/models/*/*.js',
        ],
        'web.assets_backend': [
            'hr/static/src/scss/hr.scss',
            'hr/static/src/js/chat_mixin.js',
            'hr/static/src/js/hr_employee.js',
            'hr/static/src/js/language.js',
            'hr/static/src/js/m2x_avatar_employee.js',
            'hr/static/src/js/standalone_m2o_avatar_employee.js',
            'hr/static/src/js/user_menu.js',
            'hr/static/src/models/*/*.js',
        ],
        'web.qunit_suite_tests': [
            'hr/static/tests/helpers/mock_models.js',
            'hr/static/tests/m2x_avatar_employee_tests.js',
            'hr/static/tests/standalone_m2o_avatar_employee_tests.js',
        ],
        'web.assets_qweb': [
            'hr/static/src/xml/hr_templates.xml',
        ],
    },
    'license': 'LGPL-3',
}
