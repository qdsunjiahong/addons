# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for Odoo8.0
#    Copyright (C) 2016 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': u'会计分录分析',  # 模块名称
    'version': '1.0',  # 版本
    'category': 'Tool',  # 分类
    'author': 'qdodoo Technology',  # 作者
    'website': 'http://www.qdodoo.com/',  # 网址
    'summary': '会计分录分析报表',  # 摘要
    'depends': ['base'],  # 依赖模块
    'data': [
        'account_moves_report_view.xml'
        # ...
    ],  # 更新XML,CSV
    'js': [
        # 'static/src/js/account_move_reconciliation.js',
        # ...
    ],  # javascript
    'qweb': [
        # "static/src/xml/account_move_reconciliation.xml",
        # ...
    ],
    'css': [
        # 'static/src/css/account_move_reconciliation.css',
        # ...
    ],  # css样式
    'demo': [
        # 'demo/account_demo.xml',
        # ...
    ],
    'test': [
        # 'test/account_customer_invoice.yml',
        # ...
    ],  # 测试
    'application': True,  # 是否认证
    'installable': True,  # 是否可安装
    'auto_install': False,  # 是否自动安装
    'description': """
    对会计分录明细的统计报表
    """,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
