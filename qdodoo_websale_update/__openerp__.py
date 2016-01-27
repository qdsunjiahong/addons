# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': '欧度电子商务升级',
    'description': '''
    网站页面升级
    网站权限显示：
        1.自定义taylor list
        2.通过价格表控制不同客户的产品显示
        3.客户资料添加出库仓库。订单根据设置的仓库生成销售单。
        4.解决订单确定后报错的问题。
        5.付款时取消地址栏确认。
        6.付款页面显示客户预存款金额。
        7.添加付款按钮。两个作用。一个是比对订单金额是否小于预付款金额，一个是将生成的销售订单状态修改为确认。
        8.价格表双向维护。能够从产品上添加价格表。
    ''',
    'version': '1.0',  # 版本
    'category': 'Technology',  # 分类
    'author': 'qdodoo Taylor',  # 作者
    'website': 'http://www.qdodoo.com/',  # 网址
    'summary': '',  # 摘要
    'images': [],  # 模块图片
    'depends': ['base','share','account','account_voucher','hr','website_sale','hm','product','qdodoo_purchase_sale_order2'],  # 依赖模块
    'data': ['views/qdodoo_website_tempview.xml',
             'views/res_partner_inherit.xml',
             'views/qdodoo_promotion_view.xml',
             'security/ir.model.access.csv',
             'security/qdodoo_websale_update.xml',
             'views/door_deposit.xml',],
    'application': True,  # 是否认证
    'installable': True,  # 是否可安装
    'auto_install': False,  # 是否自动安装
}
