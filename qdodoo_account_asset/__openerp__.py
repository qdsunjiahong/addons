# -*- coding: utf-8 -*-
###########################################################################################
#    author:suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': "中国固定资产修改",
    'version': '1.1',
    'author': 'Qdodoo suifeng',
    'category': 'Account',
    'sequence': 21,
    'website': 'https://www.qdodoo.com',
    'description': """
修改内容：\n
1：按照中国习惯，生成折旧数据是从采购日期的下月一号开始 \n
2：折旧生成的会计凭证日期为折旧月份的最后一天 \n
    """,
    'images': [
    ],
    'depends': ['account_asset'],
    'data': [
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
