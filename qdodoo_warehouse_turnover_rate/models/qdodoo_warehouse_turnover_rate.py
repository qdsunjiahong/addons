# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import osv, fields
import datetime
import urllib2
from lxml import etree
from openerp.tools.translate import _


class qdodoo_warehouse_ratesearch(osv.Model):
    """
        库存周转率
    """
    _name = 'qdodoo.warehouse.ratesearch'

    # 字段定义
    _columns = {
        'from_date': fields.datetime('从', select=True, required=True),
        'to_date': fields.datetime('到', select=True, required=True),
        'invoice_state': fields.selection([('pay', '支付'), ('processed', '待处理和支付'), ('draft', '草稿、待处理和支付')], select=True,
                                          string='发票状态'),

    }
    # _defaults = {
    #     'from_date':False,
    # }

    def action_open_new_window(self, cr, uid, ids, context=None):
        balance_dict = {}
        # 得到期初库存
        balance_obj = self.pool.get('qdodoo.previous.balance')
        turnrate_obj = self.pool.get('qdodoo.warehose.turnrate')
        stock_id = self.pool.get('stock.location')
        product_id = self.pool.get('product.product')
        quant_id = self.pool.get('stock.quant')
        location_dict = {}
        # 删除过去周转率
        turnrate_obj.unlink(cr, uid, turnrate_obj.search(cr, uid, []))

        search_obj = self.browse(cr, uid, ids)[0]
        location_dict2={}
        stock_move=self.pool.get('stock.move')
        location_model_cus, location_cus_ids = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_customers')
        print '1',datetime.datetime.now()
        for location in stock_id.search(cr, uid, []):
            # 从份中获取指定库位的数据

            sale_num = {}
            for quant in quant_id.browse(cr, uid, quant_id.search(cr, uid, [('location_id', '=', location)])):
                for stock_move_obj in stock_move.browse(cr,uid,stock_move.search(cr,uid,[('create_date','>=',search_obj.from_date),('create_date','<=',search_obj.to_date),('location_dest_id','=',location_cus_ids),('product_id','=',quant.product_id.id),('location_id','=',location)])):

                    if stock_move_obj.product_id.id in sale_num:
                        sale_num[stock_move_obj.product_id.id]+=stock_move_obj.product_qty
                        print 'sale_num[stock_move_obj.product_id.id]',sale_num[stock_move_obj.product_id.id]
                    else:
                        sale_num[stock_move_obj.product_id.id]=  stock_move_obj.product_qty
                        print 'sale_num[stock_move_obj.product_id.id]',sale_num[stock_move_obj.product_id.id]
            location_dict2[location] = sale_num
        # 遍历本地的库位
        print '第一次循环结束：',datetime.datetime.now()
        print '第二次循环开始：',datetime.datetime.now()
        for location in stock_id.search(cr, uid, []):
            # 从份中获取指定库位的数据
            product_dict = {}
            for quant in quant_id.browse(cr, uid, quant_id.search(cr, uid, [('location_id', '=', location)])):
                if quant.product_id.id in product_dict:
                    product_dict[quant.product_id.id] += quant.qty
                else:
                    product_dict[quant.product_id.id] = quant.qty
            location_dict[location] = product_dict
        print '第二次循环结束：',datetime.datetime.now()
        print '第三次循环开始：',datetime.datetime.now()
        for location_id in location_dict:
            location_sale_id=location_dict2.get(location_id)
            for product_id, value in location_dict[location_id].items():
                product_sale_num=location_sale_id.get(product_id)
                print 'location_id', location_id, '=====================', 'product_id', product_id, '=====================', 'date', datetime.datetime.strptime(
                    search_obj.from_date, '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=1)
                balance_ids = balance_obj.search(cr, uid,
                                                 [('location_id', '=', location_id), ('product_id', '=', product_id), (
                                                 'date', '=', datetime.datetime.strptime(search_obj.from_date,
                                                                                         '%Y-%m-%d %H:%M:%S') - datetime.timedelta(
                                                     days=1))])
                if balance_ids:
                    balance_data = balance_obj.browse(cr, uid, balance_ids[0])
                    print 'balance_data.product_id', balance_data.product_id, '=====================', 'invoice_state', search_obj.invoice_state
                    turnrate_id = turnrate_obj.create(cr, uid,
                                                      {'product': balance_data.product_id.id,
                                                       'ware_name': balance_data.location_id.id,
                                                       'beginning': balance_data.balance_num, 'final': value,
                                                       'number': product_sale_num,
                                                       'start_date': search_obj.from_date,
                                                       'end_date': search_obj.to_date,
                                                       'invoice_state': search_obj.invoice_state})
                else:
                    print 'product', product_id, '=====================', 'invoice_state', search_obj.invoice_state
                    turnrate_id = turnrate_obj.create(cr, uid,
                                                      {'product': product_id, 'ware_name': location_id,
                                                       'beginning': 0, 'final': value,
                                                       'start_date': search_obj.from_date,
                                                       'end_date': search_obj.to_date,
                                                       'number': product_sale_num,
                                                       'invoice_state': search_obj.invoice_state})
        print '第三次循环结束：',datetime.datetime.now()
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_warehouse_turnover_rate',
                                                                     'qdodoo_turnrate_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_warehouse_turnover_rate',
                                                                          'qdodoo_turnrate_form')

        view_id_form = result_form and result_form[1] or False
        return {
            'name': _('库存周转'),
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model': 'qdodoo.warehose.turnrate',
            'type': 'ir.actions.act_window',
            'views': [(view_id, 'tree'), (view_id_form, 'form')],
            'view_id': [view_id],

        }


class qdodoo_warehouse_turnover_rate(osv.Model):
    _name = 'qdodoo.warehose.turnrate'


    def compute(self, beginning, final, number):
        try:
            return number / ((beginning + final) / 2)
        except:
            return 0.0

    def _turnover_rate_compute(self, cr, uid, ids, field_name, args, context=None):
        if context == None:
            context = {}
        # 创建保存库存率的字典
        trunover_dict = {}
        for turnover_obj in self.browse(cr, uid, ids, context=context):
            trunover_dict[turnover_obj.id] = self.compute(turnover_obj.beginning, turnover_obj.final,turnover_obj.number)
        return trunover_dict
    _columns = {
        'start_date': fields.datetime('结算开始日期'),
        'end_date': fields.datetime('结算开始日期'),
        'invoice_state': fields.selection([('pay', '支付'), ('processed', '待处理和支付'), ('draft', '草稿、待处理和支付')], select=True,
                                          string='发票状态'),

        'product': fields.many2one('product.product', '产品', required=True),
        'ware_name': fields.many2one('stock.location', string='库位'),
        'beginning': fields.float(string='期初库存'),
        'final': fields.float(string='期末库存'),
        'number': fields.float(string='销售数量'),
        'turnover_rate': fields.function(_turnover_rate_compute, string='存货周转率', type='float', method=True),

    }


