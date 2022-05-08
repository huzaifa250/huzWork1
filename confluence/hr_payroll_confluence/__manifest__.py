# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Confluence HR Payroll',
    'version': '1.1',
    'author': 'IATL-IntelliSoft Software',
    'website': 'http://www.intellisoft.sd',
    'category': 'Human Resources',
    'summary': 'Provide Payroll Calculations for Confluence School',
    'description': "",
    'depends': [
        'hr_contract_confluence',
        'hr_payroll'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/salary_rules.xml',
        'views/salary_rule.xml',
        'views/contract_allowances.xml',
        'views/hr_transportation_payslip.xml',
        'report/payslip_full_details_report.xml',
        'report/payslip_salary_details_report.xml',
        'report/payslip_transportation_report.xml',
        'report/report_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
