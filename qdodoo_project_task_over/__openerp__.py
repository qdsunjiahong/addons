# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name' : 'qdodoo_project_task_over',    #模块名称
    'version' : '1.0',    #版本
    'category' : 'project_task',    #分类
    'author' : 'qdodoo Taylor',    #作者
    'website': 'http://www.qdodoo.com/',    #网址
    'summary': '计划任务升级',    #摘要
    'images' : [],    #模块图片
    'depends' : ['base','mail','project'],    #依赖模块
    'data': [
        'views/qdodoo_project_task_over_view.xml',
    ],    #更新XML,CSV
    'js': [
        # 'static/src/js/account_move_reconciliation.js',
        # ...
    ],    #javascript
    'qweb' : [
        # "static/src/xml/account_move_reconciliation.xml",
        # ...
    ],
    'css':[
        # 'static/src/css/account_move_reconciliation.css',
        # ...
    ],    #css样式
    'demo': [
        # 'demo/account_demo.xml',
        # ...
    ],
    'test': [
        # 'test/account_customer_invoice.yml',
        # ...
    ],    #测试
    'application': True,    #是否认证
    'installable': True,    #是否可安装
    'auto_install': False,    #是否自动安装
    'description' : """
    任务等级增加  任务完成事件添加
    """,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

