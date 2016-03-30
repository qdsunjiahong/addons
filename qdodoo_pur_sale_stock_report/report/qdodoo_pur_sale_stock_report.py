# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp.osv import fields, osv
from openerp import tools
import time
import datetime
from openerp.report import report_sxw
from openerp.tools.translate import _
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class qdodoo_pur_sale_stock_report(report_sxw.rml_parse):
    def employee_get(self):
        now_date = datetime.datetime.now().strftime('%Y-%m-%d')
        data = []
        # 获取查询条件中的开始时间和结束时间
        start_date = (datetime.datetime.strptime(self.start_date,'%Y-%m-%d') + datetime.timedelta(days=-1)).strftime('%Y-%m-%d') + ' 15:00:00'
        end_date = (self.end_date if self.end_date else now_date) + ' 15:59:59'
        # 获取产品的前期结余数量、本期结余数量
        balance_obj = self.pool.get('qdodoo.previous.balance')
        quant_obj = self.pool.get('stock.quant')
        move_obj = self.pool.get('stock.move')
        location_obj = self.pool.get('stock.location')
        balance_num_dict = {} #{产品:数量}
        # 组织所有产品列表
        product_list = []
        # 获取昨天的日期
        yesterday = (datetime.datetime.strptime(self.start_date,'%Y-%m-%d') - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        balance_ids = balance_obj.search(self.cr, self.uid, [('date','=',yesterday),('location_id','=',self.location_id)])
        for balance_id in balance_obj.browse(self.cr, self.uid, balance_ids):
            balance_num_dict[balance_id.product_id.id] = balance_id.balance_num
            product_list.append(balance_id.product_id)
        # 本期结余
        balance_num_new_dict = {} #{产品:数量}
        if self.end_date and self.end_date < now_date:
            # 结束日期不是当天，数据已存数据库
            balance_ids_new = balance_obj.search(self.cr, self.uid, [('date','=',self.end_date),('location_id','=',self.location_id)])
            for balance_id_new in balance_obj.browse(self.cr, self.uid, balance_ids_new):
                balance_num_new_dict[balance_id_new.product_id.id] = balance_id_new.balance_num
                if balance_id_new.product_id not in product_list:
                    product_list.append(balance_id_new.product_id)
        else:
            # 结束日期为当天，查询当前的库存
            quant_ids = quant_obj.search(self.cr, self.uid, [('location_id', '=', self.location_id)])
            for quant in quant_obj.browse(self.cr, self.uid, quant_ids):
                if quant.product_id.id in balance_num_new_dict:
                    balance_num_new_dict[quant.product_id.id] += quant.qty
                else:
                    balance_num_new_dict[quant.product_id.id] = quant.qty
                if quant.product_id not in product_list:
                    product_list.append(quant.product_id)
        location_ids = location_obj.browse(self.cr, self.uid, self.location_id)
        # 供应商库位
        supplier_location = location_obj.search(self.cr, self.uid, [('usage','=','supplier'),'|',('company_id','=',location_ids.company_id.id),('company_id','=',False)])
        # 客户库位
        customer_location = location_obj.search(self.cr, self.uid, [('usage','=','customer'),'|',('company_id','=',location_ids.company_id.id),('company_id','=',False)])
        # 盘点库位
        inventory_location = location_obj.search(self.cr, self.uid, [('usage','=','inventory'),'|',('company_id','=',location_ids.company_id.id),('company_id','=',False)])
        # 生产库位
        production_location = location_obj.search(self.cr, self.uid, [('usage','=','production'),'|',('company_id','=',location_ids.company_id.id),('company_id','=',False)])
        # 查询产品的采购数量{产品:数量}
        num_dict = {}
        move_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','in',supplier_location),('location_dest_id','=',self.location_id)])
        for move_id in move_obj.browse(self.cr, self.uid, move_ids):
            if move_id.product_id.id in num_dict:
                num_dict[move_id.product_id.id] += move_id.product_uom_qty
            else:
                num_dict[move_id.product_id.id] = move_id.product_uom_qty
            if move_id.product_id not in product_list:
                product_list.append(move_id.product_id)
        # 查询产品的采购退货数量
        num_old_dict = {}
        move_old_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_dest_id','in',supplier_location),('location_id','=',self.location_id)])
        for move_old_id in move_obj.browse(self.cr, self.uid, move_old_ids):
            if move_old_id.product_id.id in num_old_dict:
                num_old_dict[move_old_id.product_id.id] += move_old_id.product_uom_qty
            else:
                num_old_dict[move_old_id.product_id.id] = move_old_id.product_uom_qty
            if move_old_id.product_id not in product_list:
                product_list.append(move_old_id.product_id)
        # 查询产品的调拨入库数量
        move_in_dict = {}
        move_in_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('picking_type_id.code','=','internal'),('location_dest_id','=',self.location_id)])
        for move_in_id in move_obj.browse(self.cr, self.uid, move_in_ids):
            if move_in_id.product_id.id in move_in_dict:
                move_in_dict[move_in_id.product_id.id] += move_in_id.product_uom_qty
            else:
                move_in_dict[move_in_id.product_id.id] = move_in_id.product_uom_qty
            if move_in_id.product_id not in product_list:
                product_list.append(move_in_id.product_id)
        # 查询产品的调拨出库数量
        move_out_dict = {}
        move_out_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',self.location_id),('picking_type_id.code','=','internal')])
        for move_out_id in move_obj.browse(self.cr, self.uid, move_out_ids):
            if move_out_id.product_id.id in move_out_dict:
                move_out_dict[move_out_id.product_id.id] += move_out_id.product_uom_qty
            else:
                move_out_dict[move_out_id.product_id.id] = move_out_id.product_uom_qty
            if move_out_id.product_id not in product_list:
                product_list.append(move_out_id.product_id)
        # 查询产品的销售出库数量
        sale_out_dict = {}
        sale_out_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',self.location_id),('location_dest_id','in',customer_location)])
        for sale_out_id in move_obj.browse(self.cr, self.uid, sale_out_ids):
            if sale_out_id.product_id.id in sale_out_dict:
                sale_out_dict[sale_out_id.product_id.id] += sale_out_id.product_uom_qty
            else:
                sale_out_dict[sale_out_id.product_id.id] = sale_out_id.product_uom_qty
            if sale_out_id.product_id not in product_list:
                product_list.append(sale_out_id.product_id)
        # 查询产品销售退货数量
        sale_in_dict = {}
        sale_in_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','in',customer_location),('location_dest_id','=',self.location_id)])
        for sale_in_id in move_obj.browse(self.cr, self.uid, sale_in_ids):
            if sale_in_id.product_id.id in sale_in_dict:
                sale_in_dict[sale_in_id.product_id.id] += sale_in_id.product_uom_qty
            else:
                sale_in_dict[sale_in_id.product_id.id] = sale_in_id.product_uom_qty
            if sale_in_id.product_id not in product_list:
                product_list.append(sale_in_id.product_id)
        # 查询产品的盘点盈亏数量
        inventory_dict = {}
        inventory_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','in',inventory_location),('location_dest_id','=',self.location_id)])
        for inventory_id in move_obj.browse(self.cr, self.uid, inventory_ids):
            if inventory_id.product_id.id in inventory_dict:
                inventory_dict[inventory_id.product_id.id] -= inventory_id.product_uom_qty
            else:
                inventory_dict[inventory_id.product_id.id] = -inventory_id.product_uom_qty
            if inventory_id.product_id not in product_list:
                product_list.append(inventory_id.product_id)
        inventory_in_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',self.location_id),('location_dest_id','in',inventory_location)])
        for inventory_in_id in move_obj.browse(self.cr, self.uid, inventory_in_ids):
            if inventory_in_id.product_id.id in inventory_dict:
                inventory_dict[inventory_in_id.product_id.id] += inventory_in_id.product_uom_qty
            else:
                inventory_dict[inventory_in_id.product_id.id] = inventory_in_id.product_uom_qty
            if inventory_in_id.product_id not in product_list:
                product_list.append(inventory_in_id.product_id)
        # 查询产品的生产数量
        production_dict = {}
        production_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','in',production_location),('location_dest_id','=',self.location_id)])
        for production_id in move_obj.browse(self.cr, self.uid, production_ids):
            if production_id.product_id.id in production_dict:
                production_dict[production_id.product_id.id] += production_id.product_uom_qty
            else:
                production_dict[production_id.product_id.id] = production_id.product_uom_qty
            if production_id.product_id not in product_list:
                product_list.append(production_id.product_id)
        # 查询产品的原料消耗
        production_old_dict = {}
        production_old_ids = move_obj.search(self.cr, self.uid, [('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',self.location_id),('location_dest_id','in',production_location)])
        for production_old_id in move_obj.browse(self.cr, self.uid, production_old_ids):
            if production_old_id.product_id.id in production_old_dict:
                production_old_dict[production_old_id.product_id.id] += production_old_id.product_uom_qty
            else:
                production_old_dict[production_old_id.product_id.id] = production_old_id.product_uom_qty
            if production_old_id.product_id not in product_list:
                product_list.append(production_old_id.product_id)
        # 循环所有产品
        for product_l in product_list:
            val_dict = {}
            val_dict['start_date'] = self.start_date #开始时间
            val_dict['end_date'] = self.end_date if self.end_date else now_date #截止时间
            val_dict['location_id'] = location_ids.complete_name.split('/',1)[1] if location_ids.location_id else location_ids.complete_name #库位名字
            val_dict['product_id'] = product_l.default_code #产品编号
            val_dict['product_name'] = product_l.name_template #产品名称
            val_dict['product_category'] = product_l.categ_id.complete_name #产品分类
            previous_balance_num = str(balance_num_dict.get(product_l.id,0.0))
            val_dict['previous_balance_num'] = previous_balance_num[:previous_balance_num.index('.')+5] #前期结余数量
            purchase_stock_num = str(num_dict.get(product_l.id,0.0))
            val_dict['purchase_stock_num'] = purchase_stock_num[:purchase_stock_num.index('.')+5] #采购入库数量
            purchase_stock_old_num = str(num_old_dict.get(product_l.id,0.0))
            val_dict['purchase_stock_old_num'] = purchase_stock_old_num[:purchase_stock_old_num.index('.')+5] #采购退货数量
            move_stock_num = str(move_in_dict.get(product_l.id,0.0))
            val_dict['move_stock_num'] = move_stock_num[:move_stock_num.index('.')+5] #调拨入库数量
            sale_stock_num = str(sale_out_dict.get(product_l.id,0.0))
            val_dict['sale_stock_num'] = sale_stock_num[:sale_stock_num.index('.')+5] #销售出库数量
            sale_stock_old_num = str(sale_in_dict.get(product_l.id,0.0))
            val_dict['sale_stock_old_num'] = sale_stock_old_num[:sale_stock_old_num.index('.')+5] #销售退货数量
            move_stock_out_num = str(move_out_dict.get(product_l.id,0.0))
            val_dict['move_stock_out_num'] = move_stock_out_num[:move_stock_out_num.index('.')+5] #调拨出库数量
            inventory_num = str(inventory_dict.get(product_l.id,0.0))
            val_dict['inventory_num'] = inventory_num[:inventory_num.index('.')+5] #盘点盈亏数量
            scrap_num = str(0.0)
            val_dict['scrap_num'] = scrap_num[:scrap_num.index('.')+5] #报废数量
            mrp_num = str(production_dict.get(product_l.id,0.0))
            val_dict['mrp_num'] = mrp_num[:mrp_num.index('.')+5] #生产数量
            mrp_old_num = str(production_old_dict.get(product_l.id,0.0))
            val_dict['mrp_old_num'] = mrp_old_num[:mrp_old_num.index('.')+5] #原料消耗数量
            current_balance_num = str(balance_num_new_dict.get(product_l.id,0.0))
            val_dict['current_balance_num'] = current_balance_num[:current_balance_num.index('.')+5] #本期结余数量
            data.append(val_dict)
        if not data:
            data = [{'start_date':self.start_date,'end_date':self.end_date if self.end_date else now_date,'location_id':self.location_id,'product_name':'',
                     'product_id':'','product_category':'','previous_balance_num':'','previous_balance_amount':'','purchase_stock_num':'','purchase_stock_amount':'','purchase_stock_old_num':'',
                     'purchase_stock_old_amount':'','move_stock_num':'','move_stock_amount':'','sale_stock_num':'','sale_stock_amount':'','sale_stock_old_num':'',
                     'sale_stock_old_amount':'','move_stock_out_num':'','move_stock_out_amount':'','inventory_num':'',
                     'inventory_amount':'','scrap_num':'','scrap_amount':'','mrp_num':'','mrp_amount':'','current_balance_num':'','current_balance_amount':''}]
        return data

    def __init__(self, cr, uid, name, context):
        self.start_date = context.get('start_date','')
        self.end_date = context.get('end_date','')
        self.location_id = context.get('location_id','')
        super(qdodoo_pur_sale_stock_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr': cr,
            'uid': uid,
            'employee': self.employee_get
        })

class report_accounts_receivable(osv.AbstractModel):
    _name = 'report.qdodoo_pur_sale_stock_report.report_pur_sale_stock'
    _inherit = 'report.abstract_report'
    _template = 'qdodoo_pur_sale_stock_report.report_pur_sale_stock'
    _wrapped_report_class = qdodoo_pur_sale_stock_report
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

