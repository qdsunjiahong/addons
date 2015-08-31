# -*- coding: utf-8 -*-
{
    'name': '雨水产品扩展模块',
    'category': 'Product',
    'summary': '雨水产品扩展模块功能',
    'version': '1.0',
    'description': """
雨水产品扩展模块
====================================================
    1.增加产品的导入功能:
        产品通过excel模板导入到Odoo中
        """,
    'author': 'sun',
    'depends': ['product'],
    'data': [
        'views/product.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
