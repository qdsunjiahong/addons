# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name' : '汽车进口贸易',    #模块名称
    'version' : '1.0',    #版本
    'category' : 'Technology',    #分类
    'author' : 'qdodoo Technology',    #作者
    'website': 'http://www.qdodoo.com/',    #网址
    'summary': '',    #摘要
    'images' : [],    #模块图片
    'depends' : ['base','mail','purchase','account_payment','product','account_voucher','report'],    #依赖模块
    'data': [
        'qdodoo_car_operations_view.xml',
        'qdodoo_car_archives_view.xml',
        'views/report_qdodoo_car_import.xml',
        'views/report_qdodoo_entrusted_agency.xml',
        'views/report_qdodoo_car_bill_lading.xml',
        'qdodoo_car_import_trade_report.xml',
        'data/qdodoo_car_import_trade_data.xml',
        'qdodoo_car_contract_view.xml',
        'qdodoo_car_import_trade_sequence.xml',
        'qdodoo_car_import_trade_workflow.xml',
        'qdodoo_entrusted_agency_view.xml',
        'qdodoo_account_payment_workflow.xml',
        # ...
    ],    #更新XML,CSV
    'js': [
        # 'static/src/js/account_move_reconciliation.js',
        # ...
    ],    #javascript
    'qweb': ['static/src/xml/*.xml'],
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
    汽车进口贸易
    """,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: