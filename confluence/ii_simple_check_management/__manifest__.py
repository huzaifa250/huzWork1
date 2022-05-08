# -*- coding: utf-8 -*-
{
    'name': "Takreer Simple Check Management",

    'summary': """
        Simple Check Management""",

    'description': """
        Simple Check Management
    """,
    'author': "Iatl-Intellisoft",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['account'],
    'data': [

        'security/check_security.xml',
        'security/ir.model.access.csv',
        'data/check_payment_method.xml',
        'wizard/check_replacement_wizard.xml',
        'wizard/print_check_wizard.xml',
        'views/check_view.xml',
        'views/payment.xml',
        'views/inherit_views.xml',
        # Check print report
        'report/check_bank_template.xml',
        'report/reports.xml',
        'wizard/print_check_wizard.xml',
    ],
}
