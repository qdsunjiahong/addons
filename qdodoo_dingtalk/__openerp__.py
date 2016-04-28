# -*- coding: utf-8 -*-
###########################################################################################
#
#    dingding talk for OpenERP
#    Copyright (C) 2016 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': u'钉钉接口',  # 模块名称
    'version': '1.0',  # 版本
    'category': 'Technology',  # 分类
    'author': 'Adger Zhou',  # 作者
    'website': 'http://www.qdodoo.com/',  # 网址
    'summary': '钉钉相关技术接口对接模块',  # 摘要
    'depends': ['base', 'hr'],  # 依赖模块
    'data': [
        'views/qdodoo_dingding_data.xml',
        'views/qdoo_dd_configure_view.xml',
        'views/qdoo_dd_init_view.xml',
        'views/qdodoo_hr_employee.xml',
        'views/qdodoo_hr_work_details.xml',
        'views/template.xml'
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
erp人力资源与钉钉同步管理
操作步骤:
1.安装模块后，首先配置钉钉，菜单：人力资源》钉钉》钉钉配置
2.配置完成后，初始化钉钉，慎用，该功能将初始化同步钉钉与erp系统，执行删除钉钉在erp没有的部门和员工，新建钉钉没有的员工信息，以及更新已有的员工信息
3.找到计划的动作，设置为有效，即可每天定时执行同步操作
钉钉日志模块
    """,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
