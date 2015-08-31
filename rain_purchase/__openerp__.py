# -*- coding: utf-8 -*-

{
    'name': u'雨水采购销售导入模块扩展',
    'category': 'Other',
    'summary': u'雨水采购销售导入模块扩展',
    'website': 'http://www.rainsoft.com',
    'version': '1.0',
    'description': u"""
雨水采购销售导入模块扩展
=============
    1.增加通过excel导入采购订单明细的导入功能(模板在rain_purchase/doc下)
    2.增加通过excel导入销售订单明细的导入功能(模板在rain_purchase/doc下)
        """,
    'author': 'sun',
    'depends': ['purchase','sale'],
    'data': [
        'views/purchase.xml','views/sale.xml'
    ],
    'demo': [
    ],
    'application': True,
    'installable': True,
}
