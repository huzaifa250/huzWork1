# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Stock confluence',
    'version': '1.1',
    'category': 'Inventory/Inventory',
    'sequence': 100,
    'summary': 'Manage your stock and logistics activities',
    'description': "",
    'website': 'https://www.odoo.com/app/employees',
    'depends': [
        'stock',
        'openeducat_core',
        'openeducat_classroom',
    ],
    'data': [
        # 'security/hr_security.xml',
        'security/ir.model.access.csv',
        'views/stock_confluence.xml',
        'reports/teachers_stationary_uoi_report.xml',
        'reports/stationary.xml',
        'reports/delivery_slip.xml',
        'wizard/teachers_stationary_uoi_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

    'license': 'LGPL-3',
}
