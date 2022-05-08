# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Confluence HR Holidays',
    'version': '1.1',
    'author': 'IATL-IntelliSoft Software',
    'website': 'http://www.intellisoft.sd',
    'category': 'Human Resources',
    'summary': 'Provide Holidays for Confluence School',
    'description': "",
    'depends': [
        'hr_holidays'
    ],
    'data': [
        'data/allocation_cron.xml',
        'views/hr_leave_type.xml',
        'views/hr_leave.xml',
        'views/permission_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
