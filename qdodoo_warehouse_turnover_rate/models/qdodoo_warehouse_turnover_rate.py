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
        'location_id': fields.many2one('stock.location','库位',required =True),

    }
    # _defaults = {
    #     'from_date':False,
    # }
    def action_open_new_window(self, cr, uid, ids, context=None):
        print ids
        print context
        if not context:
            return
        # 保存产品id
        active_ids = context.get('active_ids')

        balance_dict = {}
        # 得到期初库存
        balance_obj = self.pool.get('qdodoo.previous.balance')
        turnrate_obj = self.pool.get('qdodoo.warehose.turnrate')
        stock_id = self.pool.get('stock.location')
        quant_id = self.pool.get('stock.quant')
        stock_move_obj = self.pool.get('stock.move')

        # 目的库位为客户
        location_model_cus, location_cus_ids = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock',
                                                                                                   'stock_location_customers')
        # 源库位不能为供应商
        location_model, location_suppliers_ids = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock',
                                                                                                     'stock_location_suppliers')
        turnrate_obj.unlink(cr, uid, {})
        # 搜索当前记录
        rate_search = self.browse(cr, uid, ids)
        # 组织数据字典
        turnon_dict = {
            'start_date': rate_search.from_date,
            'end_date': rate_search.to_date,
            'ware_name': rate_search[0].location_id.id,
        }
        # 遍历当前产品
        for active_id in active_ids:
            # 搜索balance对象
            turnon_dict['product'] = active_id
            print '==========================', rate_search[0].location_id.id
            balance_ids = balance_obj.search(cr, uid,
                                             [('location_id', '=', turnon_dict['ware_name']),
                                              ('product_id', '=', active_id), (
                                                  'date', '=', datetime.datetime.strptime(rate_search.from_date,
                                                                                          '%Y-%m-%d %H:%M:%S') - datetime.timedelta(
                                                      days=1))])
            if balance_ids:
                turnon_dict['beginning'] = balance_obj.browse(cr, uid, balance_ids, context=context)[0].balance_num
            else:
                turnon_dict['beginning'] = 0

            over_pro = balance_obj.search(cr, uid,
                                          [('location_id', '=',turnon_dict['ware_name']),
                                           ('product_id', '=', active_id), (
                                               'date', '=', rate_search.to_date)])
            if over_pro:
                turnon_dict['beginning'] = balance_obj.browse(cr, uid, over_pro, context=context)[0].balance_num
            else:
                turnon_dict['beginning'] = 0
                for quant in quant_id.browse(cr, uid,
                                             quant_id.search(cr, uid, [('location_id', '=', turnon_dict['ware_name'])])):
                    if turnon_dict['beginning'] > 0:
                        turnon_dict['beginning'] += quant.qty
                    else:
                        turnon_dict['beginning'] = quant.qty

            # 查询产品的销售出库数量
            sale_out_dict = {}
            sum = 0
            print 'product_id',active_id,'date_start', rate_search.from_date,'date_end',rate_search.to_date,'location_id',turnon_dict['ware_name'],location_cus_ids,location_suppliers_ids
            sale_out_ids = stock_move_obj.search(cr,uid,
                                                 [('product_id', '=', active_id), ('state', '=', 'done'),
                                                  ('date', '>=', rate_search.from_date),
                                                  ('date', '<=', rate_search.to_date),
                                                  ('location_id', '=', turnon_dict['ware_name']),
                                                  ('location_dest_id', '=', location_cus_ids), ('location_id','!=',location_suppliers_ids)])
            print  'idsssssssssssssssssssssssssssssssssssssssss',sale_out_ids
            for sale_out_id in stock_move_obj.browse(cr, uid, sale_out_ids):
                print '222222222222222222222222',sale_out_id
                if sum > 0:
                    sum += sale_out_id.product_uom_qty
                else:
                    sum = sale_out_id.product_uom_qty

            turnon_dict['number'] = sum
            print  turnon_dict
            turnrate_id = turnrate_obj.create(cr, uid,turnon_dict)
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



            # location_dict = {}
            # for location in stock_id.search(cr, uid, []):
            #     product_dict = {}
            #     for quant in quant_id.browse(cr, uid, quant_id.search(cr, uid, [('location_id', '=', location)])):
            #         if quant.product_id.id in product_dict:
            #             product_dict[quant.product_id.id] += quant.qty
            #         else:
            #             product_dict[quant.product_id.id] = quant.qty
            #     location_dict[location] = product_dict
            # # {库房{产品},库房{产品}}
            #
            # for location_id in location_dict:
            #     for product_id, values in location_dict[location_id].items():
            #         print 'product_id',product_id,'location_id',location_id,'location_id',location_suppliers_ids,'date_start',rate_search.from_date,'data_end',rate_search.to_date
            #         stock_ids = stock_move_obj.search(cr, uid,
            #                                     [('product_id', '=', product_id), ('location_id', '=', location_id),
            #                                      ('location_id', '!=', location_suppliers_ids), ('date','>=',rate_search.from_date),('date','<=',rate_search.to_date),('state','=','done')])
            #         # 遍历转移单
            #         sum=0#数量字典
            #         for stock_re in stock_move_obj.browse(cr, uid, stock_ids):
            #             if stock_re.location_id.id <> stock_re.location_dest_id:
            #                 if sum >0:
            #                     sum += stock_re.product_qty
            #                 else:
            #                     sum = stock_re.product_qty
            #
            #         print product_id
            #         balance_ids = balance_obj.search(cr, uid,
            #                                                 [('location_id', '=', location_id), ('product_id', '=', product_id), (
            #                                                   'date', '=', datetime.datetime.strptime(rate_search.from_date,
            #                                                                                           '%Y-%m-%d %H:%M:%S') - datetime.timedelta(
            #                                                       days=1))])
            #         print  sum
            #         if balance_ids:
            #             balance_record=balance_obj.browse(cr,uid,balance_ids)[0]
            #             turnrate_id = turnrate_obj.create(cr, uid,
            #                                                    {'product': product_id,
            #                                                     'ware_name': location_id,
            #                                                     'beginning': balance_record.balance_num, 'final': values ,
            #                                                     'number': sum,
            #                                                     'start_date': rate_search.from_date,
            #                                                     'end_date': rate_search.to_date,
            #                                                     'invoice_state': rate_search.invoice_state})
            #         else:
            #             turnrate_id = turnrate_obj.create(cr, uid,
            #                                                    {'product': product_id,
            #                                                     'ware_name': location_id,
            #                                                     'beginning': 0, 'final': values ,
            #                                                     'number': sum,
            #                                                     'start_date': rate_search.from_date,
            #                                                     'end_date': rate_search.to_date,
            #                                                     'invoice_state': rate_search.invoice_state})
            #
            # result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_warehouse_turnover_rate',
            #                                                                  'qdodoo_turnrate_tree')
            # view_id = result and result[1] or False
            # result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_warehouse_turnover_rate',
            #                                                                       'qdodoo_turnrate_form')
            #
            # view_id_form = result_form and result_form[1] or False
            # return {
            #         'name': _('库存周转'),
            #         'view_type': 'form',
            #         "view_mode": 'tree,form',
            #         'res_model': 'qdodoo.warehose.turnrate',
            #         'type': 'ir.actions.act_window',
            #         'views': [(view_id, 'tree'), (view_id_form, 'form')],
            #         'view_id': [view_id],
            #
            #     }


class qdodoo_warehouse_turnover_rate(osv.Model):
    _name = 'qdodoo.warehose.turnrate'

    def compute(self, beginning, final, number):
        try:
            return 100*number / ((beginning + final) / 2)
        except:
            return 0.0

    def _turnover_rate_compute(self, cr, uid, ids, field_name, args, context=None):
        if context == None:
            context = {}
        # 创建保存库存率的字典
        trunover_dict = {}
        for turnover_obj in self.browse(cr, uid, ids, context=context):
            trunover_dict[turnover_obj.id] = self.compute(turnover_obj.beginning, turnover_obj.final,
                                                          turnover_obj.number)
        return trunover_dict

    _columns = {
        'start_date': fields.datetime('结算开始日期'),
        'end_date': fields.datetime('结算开始日期'),
        'product': fields.many2one('product.product', '产品', required=True),
        'ware_name': fields.many2one('stock.location', string='库位'),
        'beginning': fields.float(string='期初库存'),
        'final': fields.float(string='期末库存'),
        'number': fields.float(string='销售数量'),
        'turnover_rate': fields.function(_turnover_rate_compute, string='存货周转率', type='float', method=True),

    }
