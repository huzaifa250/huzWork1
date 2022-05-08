# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

{
    'name': "Overtime B",

    'summary': """
       Calculate and Manage Employee Overtime""",

    'description': """
        Calculate and Manage Employee Overtime
    """,

    'author': "IATL Intellisoft International",
    'website': "http://www.iatl-intellisoft.com",
    'category': 'base',
    'version': '0.1',
    'depends': ['hr', 'hr_payroll', 'hr_contract', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/multi_company.xml',
        # 'data/hr_overtime_data.xml',
        'views/hr_conflunce_overtime_view.xml',

    ],
    # 'application': True,
    'auto_install': False,
    'installable': True,
}
