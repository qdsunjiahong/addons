# -*- encoding:utf-8 -*-
{
    'name': u'会计分录明细增加生产成品名称',
    'description': u"""
   # 生产模块扩展
   # ========================
   # 在会计分录增加生产产品成品名称
   """,
    'author': 'Rainsoft',
    'depends': [
        'account', 'mrp'
    ],
    'data': ['mrp_account_invoice.xml'],
    'installable': True,
    'category': 'Others',
}
