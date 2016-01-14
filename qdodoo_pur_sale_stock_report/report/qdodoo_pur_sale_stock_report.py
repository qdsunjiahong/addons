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
        start_date = self.start_date + ' 00:00:00'
        end_date = (self.end_date if self.end_date else now_date) + ' 23:59:59'
        # 根据库位id获取产品
        product_lst = []
        product_dict = {} #本期结余
        quant_id = self.pool.get('stock.quant')
        for quant in quant_id.browse(self.cr, self.uid, quant_id.search(self.cr, self.uid, [('location_id','=',self.location_id)])):
            if quant.product_id.id in product_dict:
                product_dict[quant.product_id.id] += quant.qty
            else:
                product_dict[quant.product_id.id] = quant.qty
            if quant.product_id.id not in product_lst:
                product_lst.append(quant.product_id.id)
        # 根据id获取库位名字
        location_obj = self.pool.get('stock.location')
        location_id = location_obj.browse(self.cr,self.uid,self.location_id)
        location_id_name = location_id.complete_name.split('/',1)[1] if location_id.location_id else location_id.complete_name
        # 根据id获取产品名字、内部编号、分类id
        dict_product = {}
        dict_product_name = {}
        dict_category_id = {}
        product_obj = self.pool.get('product.product')
        for product_id in product_obj.browse(self.cr,self.uid,product_lst):
            dict_product[product_id.id] = product_id.name_template
            dict_product_name[product_id.id] = product_id.default_code
            dict_category_id[product_id.id] = product_id.categ_id.id
        # 根据id获取产品分类名称
        dict_category = {}
        category_obj = self.pool.get('product.category')
        category_ids = category_obj.search(self.cr,self.uid,[])
        for category_id in category_obj.browse(self.cr,self.uid,category_ids):
            if category_id.parent_id:
                category_name = category_id.parent_id.name+' / '+category_id.name
            else:
                category_name = category_id.name
            dict_category[category_id.id] = category_name
        # 获取产品的前期结余
        balance_num_dict = {}
        balance_num_new_dict = {}
        balance_obj = self.pool.get('qdodoo.previous.balance')
        # 获取昨天的日期
        yesterday = (datetime.datetime.strptime(self.start_date,'%Y-%m-%d') - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        balance_ids = balance_obj.search(self.cr, self.uid, [('date','=',yesterday),('product_id','in',product_lst),('location_id','=',self.location_id)])
        for balance_id in balance_obj.browse(self.cr, self.uid, balance_ids):
            balance_num_dict[balance_id.product_id.id] = balance_id.balance_num
        if self.end_date:
            balance_ids_new = balance_obj.search(self.cr, self.uid, [('date','=',self.end_date),('product_id','in',product_lst),('location_id','=',self.location_id)])
            for balance_id_new in balance_obj.browse(self.cr, self.uid, balance_ids_new):
                balance_num_new_dict[balance_id_new.product_id.id] = balance_id_new.balance_num
        # 查询产品的采购数量
        num_dict = {}
        num_old_dict = {}
        move_obj = self.pool.get('stock.move')
        # 获取供应商库位
        location_model, location_ids = self.pool.get('ir.model.data').get_object_reference(self.cr, self.uid, 'stock', 'stock_location_suppliers')
        location_model_cus, location_cus_ids = self.pool.get('ir.model.data').get_object_reference(self.cr, self.uid, 'stock', 'stock_location_customers')
        location_model_inventory, location_inventory_ids = self.pool.get('ir.model.data').get_object_reference(self.cr, self.uid, 'stock', 'location_inventory')
        location_model_scrapped, location_scrapped_ids = self.pool.get('ir.model.data').get_object_reference(self.cr, self.uid, 'stock', 'stock_location_scrapped')
        location_model_production, location_production_ids = self.pool.get('ir.model.data').get_object_reference(self.cr, self.uid, 'stock', 'location_production')
        move_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',location_ids),('location_dest_id','=',self.location_id)])
        for move_id in move_obj.browse(self.cr, self.uid, move_ids):
            if move_id.product_id.id in num_dict:
                num_dict[move_id.product_id.id] += move_id.product_uom_qty
            else:
                num_dict[move_id.product_id.id] = move_id.product_uom_qty
        # 查询产品的采购退货数量
        move_old_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_dest_id','=',location_ids),('location_id','=',self.location_id)])
        for move_old_id in move_obj.browse(self.cr, self.uid, move_old_ids):
            if move_old_id.product_id.id in num_old_dict:
                num_old_dict[move_old_id.product_id.id] += move_old_id.product_uom_qty
            else:
                num_old_dict[move_old_id.product_id.id] = move_old_id.product_uom_qty
        # 查询产品的调拨入库数量
        move_in_dict = {}
        move_in_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id.usage','=','transit'),('location_dest_id','=',self.location_id)])
        for move_in_id in move_obj.browse(self.cr, self.uid, move_in_ids):
            if move_in_id.product_id.id in move_in_dict:
                move_in_dict[move_in_id.product_id.id] += move_in_id.product_uom_qty
            else:
                move_in_dict[move_in_id.product_id.id] = move_in_id.product_uom_qty
        # 查询产品的调拨出库数量
        move_out_dict = {}
        move_out_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',self.location_id),('location_dest_id.usage','=','transit')])
        for move_out_id in move_obj.browse(self.cr, self.uid, move_out_ids):
            if move_out_id.product_id.id in move_out_dict:
                move_out_dict[move_out_id.product_id.id] += move_out_id.product_uom_qty
            else:
                move_out_dict[move_out_id.product_id.id] = move_out_id.product_uom_qty
        # 查询产品的销售出库数量
        sale_out_dict = {}
        sale_out_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',self.location_id),('location_dest_id','=',location_cus_ids)])
        for sale_out_id in move_obj.browse(self.cr, self.uid, sale_out_ids):
            if sale_out_id.product_id.id in sale_out_dict:
                sale_out_dict[sale_out_id.product_id.id] += sale_out_id.product_uom_qty
            else:
                sale_out_dict[sale_out_id.product_id.id] = sale_out_id.product_uom_qty
        # 查询产品销售退货数量
        sale_in_dict = {}
        sale_in_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',location_cus_ids),('location_dest_id','=',self.location_id)])
        for sale_in_id in move_obj.browse(self.cr, self.uid, sale_in_ids):
            if sale_in_id.product_id.id in sale_in_dict:
                sale_in_dict[sale_in_id.product_id.id] += sale_in_id.product_uom_qty
            else:
                sale_in_dict[sale_in_id.product_id.id] = sale_in_id.product_uom_qty
        # 查询产品的盘点盈亏数量
        inventory_dict = {}
        inventory_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',location_inventory_ids),('location_dest_id','=',self.location_id)])
        for inventory_id in move_obj.browse(self.cr, self.uid, inventory_ids):
            if inventory_id.product_id.id in inventory_dict:
                inventory_dict[inventory_id.product_id.id] -= inventory_id.product_uom_qty
            else:
                inventory_dict[inventory_id.product_id.id] = -inventory_id.product_uom_qty
        inventory_in_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',self.location_id),('location_dest_id','=',location_inventory_ids)])
        for inventory_in_id in move_obj.browse(self.cr, self.uid, inventory_in_ids):
            if inventory_in_id.product_id.id in inventory_dict:
                inventory_dict[inventory_in_id.product_id.id] += inventory_in_id.product_uom_qty
            else:
                inventory_dict[inventory_in_id.product_id.id] = inventory_in_id.product_uom_qty
        # 查询产品报废数量
        scrap_dict = {}
        scrap_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',self.location_id),('location_dest_id','=',location_scrapped_ids)])
        for scrap_id in move_obj.browse(self.cr, self.uid, scrap_ids):
            if scrap_id.product_id.id in scrap_dict:
                scrap_dict[scrap_id.product_id.id] += scrap_id.product_uom_qty
            else:
                scrap_dict[scrap_id.product_id.id] = scrap_id.product_uom_qty
        # 查询产品的生产数量
        production_dict = {}
        production_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',location_production_ids),('location_dest_id','=',self.location_id)])
        for production_id in move_obj.browse(self.cr, self.uid, production_ids):
            if production_id.product_id.id in production_dict:
                production_dict[production_id.product_id.id] += production_id.product_uom_qty
            else:
                production_dict[production_id.product_id.id] = production_id.product_uom_qty
        # 查询产品的原料消耗
        production_old_dict = {}
        production_old_ids = move_obj.search(self.cr, self.uid, [('product_id','in',product_lst),('state','=','done'),('date','>=',start_date),('date','<=',end_date),('location_id','=',self.location_id),('location_dest_id','=',location_production_ids)])
        for production_old_id in move_obj.browse(self.cr, self.uid, production_old_ids):
            if production_old_id.product_id.id in production_old_dict:
                production_old_dict[production_old_id.product_id.id] += production_old_id.product_uom_qty
            else:
                production_old_dict[production_old_id.product_id.id] = production_old_id.product_uom_qty
        # 循环所有查询出来的数据
        for product_l in product_lst:
            val_dict = {}
            val_dict['start_date'] = self.start_date #开始时间
            val_dict['end_date'] = self.end_date if self.end_date else now_date #截止时间
            val_dict['location_id'] = location_id_name #库位名字
            val_dict['product_id'] = dict_product.get(product_l,'') #产品编号
            val_dict['product_name'] = dict_product_name.get(product_l,'') #产品名称
            val_dict['product_category'] = dict_category.get(dict_category_id.get(product_l,''),'') #产品分类
            val_dict['previous_balance_num'] = balance_num_dict.get(product_l,0.0) #前期结余数量
            val_dict['purchase_stock_num'] = num_dict.get(product_l,0.0) #采购入库数量
            val_dict['purchase_stock_old_num'] = num_old_dict.get(product_l,0.0) #采购退货数量
            val_dict['move_stock_num'] = move_in_dict.get(product_l,0.0) #调拨入库数量
            val_dict['sale_stock_num'] = sale_out_dict.get(product_l,0.0) #销售出库数量
            val_dict['sale_stock_old_num'] = sale_in_dict.get(product_l,0.0) #销售退货数量
            val_dict['move_stock_out_num'] = move_out_dict.get(product_l,0.0) #调拨出库数量
            val_dict['inventory_num'] = inventory_dict.get(product_l,0.0) #盘点盈亏数量
            val_dict['scrap_num'] = scrap_dict.get(product_l,0.0) #报废数量
            val_dict['mrp_num'] = production_dict.get(product_l,0.0) #生产数量
            val_dict['mrp_old_num'] = production_old_dict.get(product_l,0.0) #原料消耗数量
            val_dict['current_balance_num'] = balance_num_new_dict.get(product_l,product_dict.get(product_l,0.0)) #本期结余数量

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

