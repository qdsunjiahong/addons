# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import osv, fields
from openerp.tools.translate import _
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class qdodoo_search_balance_statement(osv.Model):
    _name = "qdodoo.search.balance.statement"
    _description = "search.balance.statement"
    _columns = {
        "start_date": fields.date(string=u'开始日期', required=True),
        "end_date": fields.date(string=u'结束日期'),
        'location_id': fields.many2one('stock.location', string=u'库位', required=True)
    }

    def start_date(self, cr, uid, ids, context=None):
        """
            本月初
        """

        now_date = datetime.datetime.now()
        day = str(now_date)[:8] + '01 00:00:01'
        return day

    _defaults = {
        'start_date': start_date
    }

    def balance_statement_open_window(self, cr, uid, ids, context=None):
        unlink_ids = self.pool.get("qdodoo.result.balance.statement").search(cr, uid, [])
        self.pool.get("qdodoo.result.balance.statement").unlink(cr, uid, unlink_ids)
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        if context is None:
            context = {}
        result = mod_obj.get_object_reference(cr, uid, 'qdodoo_previous_balance_oe8',
                                              'action_result_balance_statement_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result_context = {}
        data = self.read(cr, uid, ids, [])[0]
        if data['end_date'] and data['start_date'] > data['end_date']:
            raise osv.except_osv(_(u'对不起'), _(u'开始日期不能大于结束日期！'))
        # 获取查询条件中的开始时间和结束时间
        now_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = data['start_date'] + " 00:00:01"

        end_date = (data['end_date'] if data['end_date'] else now_date) + " 23:59:59"
        location_obj = self.pool.get('stock.location')
        # 获取所有库存调拨单上的产品ID并出去重复ID
        product_list = self.pool.get('product.product').search(cr, uid, [('type', '=', 'product')])

        product_dict = {}  # 本期结余
        inventory_obj = self.pool.get('stock.quant')
        location_id = data['location_id'][0]

        invent_ids = inventory_obj.search(cr, uid, [('location_id', '=', location_id)])

        for invent in inventory_obj.browse(cr, uid, invent_ids):
            if invent.product_id.id in product_dict:
                product_dict[invent.product_id.id] += invent.qty
            else:
                product_dict[invent.product_id.id] = invent.qty
        # 根据id获取库位名字
        location_brw = location_obj.browse(cr, uid, location_id, context=context)
        location_id_name = location_brw.complete_name.split('/', 1)[
            1] if location_brw.location_id else location_brw.complete_name

        # 前期结余
        balance_num_dict = {}
        balance_num_new_dict = {}
        balance_mount_dict = {}
        balance_mount_new_dict = {}
        balance_obj = self.pool.get("qdodoo.previous.balance")
        # 获取昨天的日期
        yesterday = (datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.timedelta(
            days=1)).strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        balance_ids = balance_obj.search(cr, uid, [('date', '=', yesterday), ('product_id', 'in', product_list),
                                                   ('location_id', '=', location_id)])
        for balance_brw in balance_obj.browse(cr, uid, balance_ids):
            balance_num_dict[balance_brw.product_id.id] = balance_brw.balance_num
            balance_mount_dict[balance_brw.product_id.id] = balance_brw.balance_money
        if end_date:
            balance_ids_new = balance_obj.search(cr, uid,
                                                 [('date', '=', end_date), ('location_id', '=', location_id),
                                                  ('product_id', 'in', product_list)])
            for balance_brw_new in balance_obj.browse(cr, uid, balance_ids_new):
                balance_num_new_dict[balance_brw_new.product_id.id] = balance_brw_new.balance_num
                balance_mount_new_dict[balance_brw_new.product_id.id] = balance_brw_new.balance_money

        # 根据id获取产品名字、内部编号、分类id
        dict_product = {}
        dict_product_name = {}
        dict_category_id = {}
        product_obj = self.pool.get("product.product")
        for product_brw in product_obj.browse(cr, uid, product_list):
            dict_product[product_brw.id] = product_brw.name
            dict_product_name[product_brw.id] = product_brw.default_code
            dict_category_id[product_brw.id] = product_brw.categ_id.id

        # 入库数量
        num_dict = {}
        move_in_mount = {}
        move_in_list = []
        move_obj = self.pool.get("stock.move")

        move_ids = move_obj.search(cr, uid, [('product_id', 'in', product_list), ('state', '=', 'done'),
                                             ('date', '>=', start_date), ('date', '<=', end_date),
                                             ('location_dest_id', '=', location_id)])
        for move_brw in move_obj.browse(cr, uid, move_ids):
            if move_brw.product_id.id in num_dict:
                num_dict[move_brw.product_id.id] += move_brw.product_qty
                move_in_mount[move_brw.product_id.id] += move_brw.product_qty * move_brw.price_unit
            else:
                num_dict[move_brw.product_id.id] = move_brw.product_qty
                move_in_mount[move_brw.product_id.id] = move_brw.product_qty * move_brw.price_unit
            move_in_list.append(move_brw.product_id.id)

        # 查询产品的出库数量
        move_out_dict = {}
        move_out_mount = {}
        move_out_list = []
        move_out_ids = move_obj.search(cr, uid,
                                       [('product_id', 'in', product_list), ('state', '=', 'done'),
                                        ('date', '>=', start_date), ('date', '<=', end_date),
                                        ('location_id', '=', location_id)])
        for move_out_id in move_obj.browse(cr, uid, move_out_ids):
            if move_out_id.product_id.id in move_out_dict:
                move_out_dict[move_out_id.product_id.id] += move_out_id.product_qty
                move_out_mount[move_out_id.product_id.id] += move_out_id.price_unit * move_out_id.product_qty
            else:
                move_out_dict[move_out_id.product_id.id] = move_out_id.product_qty
                move_out_mount[move_out_id.product_id.id] = move_out_id.price_unit * move_out_id.product_qty
            move_out_list.append(move_out_id.product_id.id)

        product_list_new = list(set(move_in_list + move_out_list))
        # 循环所有查询出来的数据
        for product_l in product_list_new:
            result['name'] = location_id_name  # 库位名称
            result['product_name'] = dict_product.get(product_l, '')  # 产品名称
            result['product_id'] = product_l
            result['pre_balance'] = balance_num_dict.get(product_l, 0.0)  # 前期结余数量
            result['pre_balance_mount'] = balance_mount_dict.get(product_l, 0.0)  # 前期结余金额
            result['storage_quantity_period'] = num_dict.get(product_l, 0.0)  # 本期入库数量
            result['storege_quantity_period_mount'] = move_in_mount.get(product_l, 0.0)  # 本期入库金额
            result['number_of_library'] = move_out_dict.get(product_l, 0.0)  # 本期出库数量
            result['number_of_lib_mount'] = move_out_mount.get(product_l, 0.0)  # 本期出库金额
            result['current_balance'] = balance_num_dict.get(product_l, 0.0) + num_dict.get(product_l,
                                                                                            0.0) - move_out_dict.get(
                product_l, 0.0)  # 本期结余数量
            result['current_balance_mount'] = balance_mount_dict.get(product_l, 0.0) + move_in_mount.get(product_l,
                                                                                                         0.0) - move_out_mount.get(
                product_l, 0.0)
            self.pool.get("qdodoo.result.balance.statement").create(cr, uid, result,
                                                                    context=context)

        if data['start_date']:
            result_context.update({'start_date': data['start_date']})
        if data['end_date']:
            result_context.update({'end_date': data['end_date']})
        result['context'] = str(result_context)
        return result


class qdodoo_result_balance_statement(osv.Model):
    _name = 'qdodoo.result.balance.statement'
    _description = 'qdodoo.result.balance.statement'
    _columns = {
        'product_name': fields.char(u'产品'),
        'product_id': fields.many2one('product.product', u'产品'),
        'name': fields.char(u'库位'),
        'pre_balance': fields.float(string=u'前期结余数量'),
        'pre_balance_mount': fields.float(digits=(16, 4), string=u'前期结余金额'),
        'storage_quantity_period': fields.float(string=u'本期入库数量'),
        'storege_quantity_period_mount': fields.float(digits=(16, 4), string=u'本期入库金额'),
        'number_of_library': fields.float(string=u'本期出库数量'),
        'number_of_lib_mount': fields.float(digits=(16, 4), string=u'本期出库金额'),
        'current_balance': fields.float(string=u'本期结余数量'),
        'current_balance_mount': fields.float(digits=(16, 4), string=u'本期结余金额'),

    }
