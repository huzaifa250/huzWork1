# -*- coding: utf-8 -*-
{
    'name': "Confluence Stock Internal Requisitions",

    'summary': """
        """,

    'description': """
        Allow your employees to create Internal Requisition.
    """,

    'author': "IATL International",
    'website': "http://www.iatl-sd.com",
    'license': "AGPL-3",
    'category': 'Warehouse',
    'depends': ['base', 'stock', 'hr', 'portal','purchase_request' ],
    'data': [
        'security/security_views.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/internal_request_views.xml',
        'views/stock_picking_views.xml',
        'views/hr_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_company_views.xml',
        'views/purchase_request_views.xml',
    ],
}
