# -*- coding: utf-8 -*-
###########################################################################################
#    author:Qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': "增加产品批次价格",
    'version': '1.1',
    'author': 'Qdodoo suifeng',
    'category': 'Base',
    'sequence': 21,
    'website': 'https://www.qdodoo.com',
    'description': """
1：在批次中增加价格
2：出库时，根据批次的价格产生发票，计算成本
3：生产投料时，根据批次的价格计算成本
4：盘点时，根据批次计算成本

有问题可以邮件 qdodoo@qdodoo.com
    """,
    'images': [
    ],
    'depends': ['purchase','base','sale','mrp','stock'],
    'data': [
        'qdodoo_stock_lot_price.xml',
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
