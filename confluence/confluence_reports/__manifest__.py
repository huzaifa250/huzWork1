# -*- coding: utf-8 -*-
{
    'name': "Confluence Reports",
    'version': '15.0.1.0',
    'license': 'LGPL-3',
    'category': 'Education',
    'sequence': 3,
    'summary': "Manage Reports""",
    'complexity': "easy",
    'depends': [
        'account',
        'openeducat_admission'
    ],
    'data': [
        'report/partner_ledger.xml',
        'report/grade_ledger.xml',
        'report/payment_receipt_report.xml',
        'report/parent_statement_report.xml',
        'report/report_views.xml',
    ],
    'test': [],
    'images': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
