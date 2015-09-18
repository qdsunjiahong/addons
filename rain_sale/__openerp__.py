# -*- coding: utf-8 -*-

{
    'name': u'雨水销售模块(sale)扩展',
    'category': 'Other',
    'summary': u'雨水销售模块(sale)扩展',
    'website': 'http://www.rainsoft.com',
    'version': '1.0',
    'description': u"""
雨水销售模块(sale)扩展
=============
    1.增加通过excel导入销售订单明细的导入功能(模板在rain_sale/doc下)
        """,
    'author': 'sun',
    'depends': ['sale'],
    'data': [
        'views/sale.xml'
    ],
    'demo': [
    ],
    'application': True,
    'installable': True,
}
