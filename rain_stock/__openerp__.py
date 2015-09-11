# -*- coding: utf-8 -*-

{
    'name': u'雨水stcok模块扩展',
    'category': 'Other',
    'summary': u'雨水stcok模块扩展',
    'website': 'http://www.rainsoft.com',
    'version': '1.0',
    'description': u"""
雨水stcok模块扩展
=============
    1.修改"序列号"默认规则为"YYYYmmdd001"后三位自动增长
        2014-10-20：判断前后日期的不同，重置后三位，从001开始。
    2.2014-10-20：更改"序列号"打印大小，39mm*29mm纸张。并修改模板。
        """,
    'author': 'sun',
    'depends': ['stock','rain_base'],
    'installable': True,
    'data': [
        'views/stock_sequence.xml',
        'views/report_lot_barcode.xml'
    ],
    'demo': [
    ],
    'application': True,
}
