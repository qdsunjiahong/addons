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
    ''',
    'version': '1.0',  # 版本
    'category': 'Technology',  # 分类
    'author': 'qdodoo Taylor',  # 作者
    'website': 'http://www.qdodoo.com/',  # 网址
    'summary': '',  # 摘要
    'images': [],  # 模块图片
    'depends': ['base', 'hr'],  # 依赖模块
    'data': ['views/qdodoo_website_tempview.xml'],
    'application': True,  # 是否认证
    'installable': True,  # 是否可安装
    'auto_install': False,  # 是否自动安装
}
