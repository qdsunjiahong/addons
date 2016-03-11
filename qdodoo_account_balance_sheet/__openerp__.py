# -*- coding: utf-8 -*-
###########################################################################################
#    author:qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': "中国会计-科目余额表",
    'version': '1.1',
    'author': 'Qdodoo suifeng',
    'category': 'Account',
    'sequence': 21,
    'website': 'https://www.qdodoo.com',
    'description': """
点击菜单:会计->表->科目余额表 查询科目余额 \n
1：按照会计区间查询、展示科目余额 \n
2：报表分三层: \n
**第一层:按公司组合每个科目的期初余额，借方金额，贷方金额,期末余额 \n
**第二层:点击第一层Tree视图即可查看第二层,该科目下，按照合作伙伴拆分 \n
**第三层:点击第二层即可查看合作伙伴对应明细
    """,
    'images': [
    ],
    'depends': ['account'],
    'data': [
        'wizard/qdodoo_account_balance_wizard.xml',
        'report/qdodoo_account_balance_report.xml'
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
