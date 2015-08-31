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

    def _get_previous_balance(self, cr, uid):
        '''
            记录产品当天的结余
        '''
        stock_id = self.pool.get('stock.location')
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        date = datetime.now().date()
        # 获取昨天日期
        yesteday = datetime.strftime(date - timedelta(days=1),'%Y-%m-%d')
        all_val = {}
        # 获取所有的产品数据模型
        product_ids = product_obj.browse(cr, uid, product_obj.search(cr, uid, []))
        # 获取产品数据字典{id：采购价}
        product_cost = {}
        for line in product_ids:
            product_cost[line.id] = line.standard_price
        # 循环所有的库位
        for stock in stock_id.browse(cr, uid, stock_id.search(cr, uid, [])):
            product_dict = {}
            # 获取当天所有和改库位有关的调拨单
            move_ids = move_obj.search(cr, uid, [('date','=',datetime.strftime(date,'%Y-%m-%d')),'|',('location_dest_id','=',stock.id),('location_id','=',stock.id)])
            # 循环所有的调拨单
            for move_id in move_obj.browse(cr, uid, move_ids):
                # 判断产品是否已存在
                if move_id.product_id.id in product_dict:
                    # 产品数量累加
                    # 如果是出库单，产品数量为负
                    if move_id.location_id == stock.id:
                        product_dict[move_id.product_id.id] -= move_id.product_uom_qty
                    else:
                        product_dict[move_id.product_id.id] += move_id.product_uom_qty
                else:
                    if move_id.location_id == stock.id:
                        product_dict[move_id.product_id.id] = -move_id.product_uom_qty
                    else:
                        product_dict[move_id.product_id.id] = move_id.product_uom_qty
            all_val[stock.id] = product_dict
        ids = self.search(cr, uid, [('date','=',yesteday)])
        for locat in all_val:
            for product,num in all_val[locat].items():
                res_ids = self.search(cr, uid, [('date','=',yesteday),('location_id','=',locat),('product_id','=',product)])
                if res_ids:
                    ids.remove(res_ids[0])
                    res_obj = self.browse(cr, uid, res_ids[0])
                    balance_num = num + res_obj.balance_num
                    balance_money = num*product_cost.get(product,0.0) + res_obj.balance_money
                else:
                    balance_num = num
                    balance_money = num*product_cost.get(product,0.0)
                self.create(cr, uid, {'date':date,'location_id':locat,'product_id':product,'balance_num':balance_num,'balance_money':balance_money})
        if ids:
            for te_id in ids:
                self.copy(cr, uid, te_id,{'date':date})


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: