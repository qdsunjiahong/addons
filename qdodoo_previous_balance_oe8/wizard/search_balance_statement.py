# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import except_orm


class qdodoo_search_balance_statement(models.Model):
    _name = "qdodoo.search.balance.statement"
    _description = "search.balance.statement"
    """
        库存查询报表
    """

    def start_date(self):
        """
            今天
        """
        now_date = fields.Date.today()
        return now_date

    start_date = fields.Date(string=u'开始日期', required=True, default=start_date)
    end_date = fields.Date(string=u'结束日期')
    location_id = fields.Many2one('stock.location', string=u'库位')
    product_id = fields.Many2one('product.product', string=u'产品')
    company_id = fields.Many2one('res.company', string=u'公司')

    @api.multi
    def balance_statement_open_window(self):
        # 获取数据模型
        product_obj = self.env['product.product']
        mod_obj = self.env['ir.model.data']
        balance_obj = self.env["qdodoo.previous.balance"]
        quant_obj = self.env['stock.quant']
        # 判断查询条件是否合理
        if self.end_date and self.start_date > self.end_date:
            raise except_orm(_(u'对不起'), _(u'开始日期不能大于结束日期！'))
        # 获取查询条件中的开始时间和结束时间
        now_date = fields.Date.today()
        start_date = self.start_date + " 00:00:01"
        end_date = (self.end_date if self.end_date else now_date) + " 23:59:59"
        # 前期结余数量、金额
        balance_num_dict = {}
        balance_mount_dict = {}
        # 获取昨天的日期
        yesterday = (datetime.datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - datetime.timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        # 本期结余数量、金额
        balance_num_end_dict = {}
        balance_mount_end_dict = {}
        # 如果按照公司获取对应库位
        if self.company_id:
            product_ids = product_obj.search([('company_id','=',self.company_id.id)])
            # 获取该公司的所有库位
            location_list = self.env['stock.location'].search([('company_id', '=', self.company_id.id),('usage','=','internal')])
            balance_ids = balance_obj.search([('date', '=', yesterday), ('product_id', 'in', product_ids.ids),('location_id','in',location_list.ids)])
            balance_ids_new_ids = balance_obj.search([('date', '=', self.end_date),('product_id', 'in', product_ids.ids),('location_id','in',location_list.ids)])
            quant_ids = quant_obj.search([('product_id', 'in', product_ids.ids)])
            no_location = self.env['stock.location'].search([('usage','in',('supplier','customer','inventory','production')),'|',('company_id','=',self.company_id.id),('company_id','=',False)])
            no_location_ids = tuple(no_location.ids)
        # 如果按照库位查询
        if self.location_id:
            # 获取所有的产品
            product_ids = product_obj.search([])
            balance_ids = balance_obj.search([('date', '=', yesterday),('location_id', '=', self.location_id.id)])
            balance_ids_new_ids = balance_obj.search([('date', '=', self.end_date),('location_id', '=', self.location_id.id)])
            quant_ids = quant_obj.search([('location_id', '=', self.location_id.id)])
        # 组织前期结余数据{产品：前期结余}
        for balance_brw in balance_ids:
            if balance_brw.product_id.id in balance_num_dict:
                balance_num_dict[balance_brw.product_id.id] += balance_brw.balance_num
                balance_mount_dict[balance_brw.product_id.id] += balance_brw.balance_money
            else:
                balance_num_dict[balance_brw.product_id.id] = balance_brw.balance_num
                balance_mount_dict[balance_brw.product_id.id] = balance_brw.balance_money
        # 组织本期结余数据{产品：本期结余}
        if self.end_date and self.end_date < now_date:
            # 结束日期不是当天，数据已存数据库
            for balance_id_new in balance_ids_new_ids:
                if balance_id_new.product_id.id in balance_num_end_dict:
                    balance_num_end_dict[balance_id_new.product_id.id] += balance_id_new.balance_num
                    balance_mount_end_dict[balance_id_new.product_id.id] += balance_id_new.balance_money
                else:
                    balance_num_end_dict[balance_id_new.product_id.id] = balance_id_new.balance_num
                    balance_mount_end_dict[balance_id_new.product_id.id] = balance_id_new.balance_money
        else:
            # 结束日期为当天，查询当前的库存
            for quant in quant_ids:
                if quant.location_id.usage == 'internal':
                    if quant.product_id.id in balance_num_end_dict:
                        balance_num_end_dict[quant.product_id.id] += quant.qty
                        balance_mount_end_dict[quant.product_id.id] += quant.inventory_value
                    else:
                        balance_num_end_dict[quant.product_id.id] = quant.qty
                        balance_mount_end_dict[quant.product_id.id] = quant.inventory_value
        # 组织数据{产品：{前期结余数量、前期结余金额、本期入库数量、本期入库金额、本期出库数量、本期出库金额、本期结余数量、本期结余金额}}
        info_dict = {}
        for product_id in product_ids:
            info_dict[product_id] = {}
            log = 0
            # 前期结余数量、前期金额、本期数量、本期金额
            info_dict[product_id]['pre_balance'] = balance_num_dict.get(product_id.id,0.0)
            if not info_dict[product_id]['pre_balance']:
                log += 1
            info_dict[product_id]['pre_balance_amount'] = balance_mount_dict.get(product_id.id,0.0)
            if not info_dict[product_id]['pre_balance_amount']:
                log += 1
            info_dict[product_id]['current_balance'] = balance_num_end_dict.get(product_id.id,0.0)
            if not info_dict[product_id]['current_balance']:
                log += 1
            info_dict[product_id]['current_balance_amount'] = balance_mount_end_dict.get(product_id.id,0.0)
            if not info_dict[product_id]['current_balance_amount']:
                log += 1
            # 查询满足条件的调拨单
            # 本期入库数量、金额（采购入库、销售退货、生产入库、盘盈）
            if self.company_id:
                sql1 = """select product_uom_qty,tfs_price_unit,price_unit from stock_move where state='done' and product_id=%s and date >='%s' and date <='%s' and location_id in %s and location_dest_id not in %s"""%(product_id.id,start_date,end_date,no_location_ids,no_location_ids)
            if self.location_id:
                sql1 = """select product_uom_qty,tfs_price_unit,price_unit from stock_move where state='done' and product_id=%s and date >='%s' and date <='%s' and location_dest_id=%s"""%(product_id.id,start_date,end_date,self.location_id.id)
            self._cr.execute(sql1)
            move_ids = self._cr.fetchall()
            if not move_ids:
                log += 1
            for move_id in move_ids:
                if move_id[2]:
                    new_price = move_id[2]
                else:
                    new_price = move_id[1]
                info_dict[product_id]['storage_quantity_period'] = info_dict[product_id].get('storage_quantity_period',0.0) + move_id[0]
                info_dict[product_id]['storage_quantity_amount'] = info_dict[product_id].get('storage_quantity_amount',0.0) + (move_id[0] * new_price)
            # 本期出库数量、金额（销售出库、采购退货、原材料生产、盘亏）
            if self.company_id:
                sql2 = """select product_uom_qty,tfs_price_unit, price_unit from stock_move where state='done' and product_id=%s and date >='%s' and date <='%s' and location_dest_id in %s and location_id not in %s"""%(product_id.id,start_date,end_date,no_location_ids,no_location_ids)
            if self.location_id:
                sql2 = """select product_uom_qty,tfs_price_unit, price_unit from stock_move where state='done' and product_id=%s and date >='%s' and date <='%s' and location_id=%s"""%(product_id.id,start_date,end_date,self.location_id.id)
            self._cr.execute(sql2)
            move_out_ids = self._cr.fetchall()
            if not move_out_ids:
                log += 1
            for move_id in move_out_ids:
                if move_id[2]:
                    new_price = move_id[2]
                else:
                    new_price = move_id[1]
                info_dict[product_id]['number_of_library'] = info_dict[product_id].get('number_of_library',0.0) + move_id[0]
                info_dict[product_id]['number_of_library_amount'] = info_dict[product_id].get('number_of_library_amount',0.0) + (move_id[0] * new_price)
            if log == 6:
                info_dict.pop(product_id)
        # 创建报表展示中数据
        result_list = []
        for key,value in info_dict.items():
            sql = """insert into qdodoo_result_balance_statement (product_name,product_id,name,pre_balance,pre_balance_amount,storage_quantity_period,storage_quantity_amount,number_of_library,number_of_library_amount,current_balance,current_balance_amount,company_id) VALUES ('%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id"""%(
            key.name,key.id,self.location_id.complete_name if self.location_id else '',value.get('pre_balance',0.0),value.get('pre_balance_amount',0.0),value.get('storage_quantity_period',0.0),value.get('storage_quantity_amount',0.0),value.get('number_of_library',0.0),value.get('number_of_library_amount',0.0),value.get('current_balance',0.0),value.get('current_balance_amount',0.0),key.company_id.id
            )
            self._cr.execute(sql)
            return_obj = self.env.cr.fetchall()
            if return_obj:
                result_list.append(return_obj[0][0])
        if self.location_id:
            view_model, view_id = mod_obj.get_object_reference('qdodoo_previous_balance_oe8',
                                                               'view_result_balance_statement_tree')
            return {
                'name': _('库存结余报表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.result.balance.statement',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', result_list)],
                'views': [(view_id, 'tree')],
                'view_id': [view_id],
            }
        if self.company_id:
            view_model, view_id = mod_obj.get_object_reference('qdodoo_previous_balance_oe8',
                                                               'view_result_balance_statement_tree2')
            return {
                'name': _('库存结余报表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.result.balance.statement',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', result_list)],
                'views': [(view_id, 'tree')],
                'view_id': [view_id],
            }


class qdodoo_result_balance_statement(models.TransientModel):
    _name = 'qdodoo.result.balance.statement'
    _description = 'qdodoo.result.balance.statement'

    product_name = fields.Char(u'产品')
    product_id = fields.Many2one('product.product', u'产品')
    name = fields.Char(u'库位')
    pre_balance = fields.Float(string=u'前期结余数量')
    pre_balance_amount = fields.Float(string=u'前期结余金额', digits=(16, 4))
    storage_quantity_period = fields.Float(string=u'本期入库数量')
    storage_quantity_amount = fields.Float(string=u'本期入库金额', digits=(16, 4))
    number_of_library = fields.Float(string=u'本期出库数量')
    number_of_library_amount = fields.Float(string=u'本期出库金额', digits=(16, 4))
    current_balance = fields.Float(string=u'本期结余数量')
    current_balance_amount = fields.Float(string=u'本期结余金额', digits=(16, 4))
    company_id = fields.Many2one('res.company', string=u'公司')
