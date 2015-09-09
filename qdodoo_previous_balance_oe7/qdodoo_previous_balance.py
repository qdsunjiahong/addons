# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from datetime import datetime,timedelta


class qdodoo_previous_balance(models.Model):
    """
        存储物品明细账前期结余的数据
    """
    _name = 'qdodoo.previous.balance'    # 模型名称
    _description = 'qdodoo.previous.balance'    # 模型描述

    location_id = fields.Many2one('stock.location',u'库位')
    product_id = fields.Many2one('product.product',u'产品')
    date = fields.Date(u'日期')
    balance_num = fields.Float(u'结余数量')
    balance_money = fields.Float(u'结余金额')

    def _create_new_data(self, cr, uid):
        """
            前期结余数据初始化
        """
        quant_id = self.pool.get('stock.quant')
        stock_id = self.pool.get('stock.location')
        product_id = self.pool.get('product.product')
        location_dict = {}
        date = datetime.now().date()
        # 获取产品数据字典{id：采购价}
        product_cost = {}
        for line in product_id.browse(cr, uid, product_id.search(cr, uid, [])):
            product_cost[line.id] = line.standard_price
        # 循环所有的库位
        for location in stock_id.search(cr, uid, []):
            product_dict = {}
            # 从份中获取指定库位的数据
            for quant in quant_id.browse(cr, uid, quant_id.search(cr, uid, [('location_id','=',location)])):
                if quant.product_id.id in product_dict:
                    product_dict[quant.product_id.id] += quant.qty
                else:
                    product_dict[quant.product_id.id] = quant.qty
            location_dict[location] = product_dict
        for location_id in location_dict:
            for product_id,value in location_dict[location_id].items():
                self.create(cr, uid, {'location_id':location_id,'product_id':product_id,'date':date,'balance_num':value,'balance_money':value*product_cost.get(product_id,0.0)})



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: