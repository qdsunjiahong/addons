# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name' : 'qdodoo_order_default_sort',    #模块名称
    'version' : '1.0',    #版本
    'category' : 'other',    #分类
    'author' : 'qdodoo Taylor',    #作者
    'website': 'http://www.qdodoo.com/',    #网址
    'summary': '根据日期倒序',    #摘要
    'images' : [],    #模块图片
    'depends' : ['base','mail','procurement','stock','mrp'],    #依赖模块
    'data': [
        # 'security/account_security.xml',
        # ...
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
    入库单、内部调拨、送货单、需求单、库存调拨、生产单
    一、	单据查询默认按倒序排列
    """,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
