# -*- coding: utf-8 -*-
{
    'name': u'雨水采购合同扩展',
    'category': 'Other',
    'summary': u'雨水采购合同扩展',
    'website': 'http://www.rainsoft.com',
    'version': '1.0',
    'description': u"""
雨水采购合同扩展
=============
    添加合同编号、合同名称、合同有效期、合同类型（临时、长期）、合同使用单位。
        """,
    'author': 'tiger',
    'depends': ['purchase'],
    'data': [
        'views/contract_views.xml'
    ],
    'demo': [
    ],
    'application': True,
    'installable': True,
}