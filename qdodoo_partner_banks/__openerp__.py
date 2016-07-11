# -*- coding: utf-8 -*-
{
    'name': "qdodoo_partner_banks",

    'summary': """
        显示供应商帐户列表""",

    'description': """
        显示供应商帐户列表
    """,

    'author': "Donald",
    'website': "http://www.qdodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'partner_banks_view.xml',
    ],
    # only loaded in demonstration mode
}