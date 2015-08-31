# -*- coding: utf-8 -*-

{
    'name': 'Rain Account Extention',
    'version': '1.0',
    'category': 'Other',
    'sequence': 14,
    'summary': '',
    'description': """
财务模块扩展
==============
1.让会计凭证显示数量
2.差异分摊
3.导入会计凭证的分录明细（会计->周期性处理）
　
""",
    'author': 'sun',
    'website': '',
    'depends': ['account'],
    'data': [
        'views/account.xml'
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}