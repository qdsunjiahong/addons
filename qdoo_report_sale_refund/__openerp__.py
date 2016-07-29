# -*- coding: utf-8 -*-
{
    'name': "qdoo_report_sale_refund",

    'summary': """
        销售及退货报表""",

    'description': """
        销售及退货报表
    """,

    'author': "Caihong",
    'website': "http://www.qdodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '8.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'qdoo_invoice_report_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo.xml',
    ],
}