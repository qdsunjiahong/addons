# -*- coding: utf-8 -*-
##############################################################################
# OpenERP Connector
# Copyright 2013 Amos <sale@100china.cn>
##############################################################################
{
    "name": "Amos Group 用户规则生成器",
    "version": "1.0",
    'author' : 'Amos',
    'website' : 'www.100china.cn',
    "category": "base",
    'depends' : ['base'],
    'data': [
        'amos_res_groups_configure_view.xml',
        'base_data.xml',
             ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'description': """
对于使用ID设计权限
====================================

作用域:
--------------------------------------------
    * 可以根据用户的默认值来动态生成不同的权限功能，简化设置时间
""",
}