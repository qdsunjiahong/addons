# -*- encoding: utf-8 -*-
###########################################################################################
#
#    qdodoo.account.contract_last for OpenERP
#    Copyright (C) 2016 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': u'当前合同状态',
    'author': 'qdodoo Technology',
    'version': '0.1',
    'depends': ['base'],
    'category' : 'Other',
    'summary': '最近合同状态列表',
    'description': """
最近合同状态列表.
================================

与各供货商最近的合同状态列表
    """,
    'data': [
        'qdodoo_account_contract_last.xml',
    ],
    'demo': [],
    'installable': True,  #是否可安装
    'website': 'http://www.qdodoo.com/',
    'application' : True,  #是否认证
    'auto_install': False,    #是否自动安装
    #'certificate' : '001292377792581874189',
}
