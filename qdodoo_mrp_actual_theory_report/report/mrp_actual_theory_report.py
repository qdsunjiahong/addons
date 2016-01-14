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


class qdodoo_mrp_actual_theory_report(report_sxw.rml_parse):

    # 根据生产单获取bom中的比例
    def get_bom_inf(self, mrp_obj):
        # 获取bom信息
        bom_id = mrp_obj.bom_id
        # 获取产品-数量
        product_qty_dict = {}
        # 获取产成品总数量
        num = bom_id.product_qty
        product_qty_dict[mrp_obj.product_id.id] = num
        for line in bom_id.sub_products:
            product_qty_dict[line.product_id.id] = line.product_qty
            num += line.product_qty
        # 获取原材料数量
        product_unit_num={}
        for line in bom_id.bom_line_ids:
            product_unit_num[line.product_id.id] = line.product_qty
        # 更新生产单中产品比例
        product_unit_dict = {}
        for key, value in product_qty_dict.items():
            product_unit_dict[key] = value / num
        return product_unit_dict,product_unit_num,product_qty_dict

    # 根据生产单和原料获取分摊的数量
    def get_inventory_num(self, mrp_id, product_id):
        inventory_obj = self.pool.get('qdodoo.stock.inventory.report2')
        inventory_ids = inventory_obj.search(self.cr, self.uid, [('mo_id','=',mrp_id),('product_id','=',product_id)])
        if inventory_ids:
            return inventory_obj.browse(self.cr, self.uid, inventory_ids[0]).product_qty
        else:
            return 0.0

    def employee_get(self):
        now_date = datetime.datetime.now().strftime('%Y-%m-%d ')
        data = []
        # 获取查询条件中的开始时间和结束时间
        start_date = self.start_date + ' 00:00:00'
        end_date = (self.end_date if self.end_date else now_date) + ' 23:59:59'
        # 查询满足条件的所有完成的生产单
        mrp_obj = self.pool.get('mrp.production')
        domain = [('state','=','done'),('date_planned','>=',start_date),('date_planned','<=',end_date)]
        if self.analytic_plan:
            domain +=  [('analytic_account','=',self.analytic_plan)]
        if self.product_id:
            domain +=  [('product_id','=',self.product_id)]
        if self.mrp_production:
            domain +=  [('id','=',self.mrp_production)]
        if self.location_id[0][2]:
            domain +=  [('location_dest_id','in',','.join([str(i) for i in self.location_id[0][2]]))]
        mrp_ids = mrp_obj.search(self.cr, self.uid, domain)
        # 如果没有生产单，返回空值
        if not mrp_ids:
            data = [{'start_date':self.start_date,'end_date':self.end_date if self.end_date else now_date,'production_name':'','production_id':'',
                     'product_id':'','actual_money':'','actual_consumption_num':'','inventory':'','share_num':'','actual_price':'','theory_num':'','theory_money':'','theory_price':'',
                     'save_number':'','save_money':'','average_number':'','average_money':''}]
            return data
        # 循环所有的生产单，组织数据{生产单号:{产成品id:{原料:{投料数量，分摊数量。。。}},数量:,库位:,辅助核算:}}
        all_date = {}
        for mrp_id in mrp_obj.browse(self.cr, self.uid, mrp_ids):
            unit_dict,number_dict,product_new_dict = self.get_bom_inf(mrp_id)
            # 产成品信息
            mrp_dict = {}
            # 获取产成品
            for line_product in mrp_id.move_created_ids2:
                if line_product.state =='done':
                    mrp_dict[line_product.product_id] = {}
                    mrp_dict[line_product.product_id]['product_number'] = line_product.product_uom_qty
                    mrp_dict[line_product.product_id]['location_id'] = mrp_id.location_dest_id.name
                    mrp_dict[line_product.product_id]['analytic_plan'] = mrp_id.analytic_account.name
                    # 获取已投料数据
                    raw_obj_dict = {}
                    for line_raw in mrp_id.move_lines2:
                        if line_raw.state == 'done':
                            if line_raw.product_id in raw_obj_dict:
                                raw_obj_dict[line_raw.product_id]['inventory'] += line_raw.product_uom_qty * unit_dict.get(line_product.product_id.id,0)
                            else:
                                raw_obj_dict[line_raw.product_id] = {}
                                raw_obj_dict[line_raw.product_id]['inventory'] = line_raw.product_uom_qty * unit_dict.get(line_product.product_id.id,0)
                                raw_obj_dict[line_raw.product_id]['price_unit'] = line_raw.price_unit
                                if not product_new_dict.get(line_product.product_id.id):
                                    raw_obj_dict[line_raw.product_id]['theory_num'] = 0
                                else:
                                    raw_obj_dict[line_raw.product_id]['theory_num'] = number_dict.get(line_raw.product_id.id,0) * line_product.product_uom_qty/product_new_dict.get(line_product.product_id.id) * unit_dict.get(line_product.product_id.id,0)
                    mrp_dict[line_product.product_id]['raw'] = raw_obj_dict
            all_date[mrp_id] = mrp_dict
        # 组织报表数据
        for all_key,all_value in all_date.items():
            for two_key,two_value in all_value.items():
                for three_key,three_value in two_value['raw'].items():
                    date_line = {}
                    date_line['start_date'] = self.start_date #开始时间
                    date_line['end_date'] = self.end_date if self.end_date else now_date #结束时间
                    date_line['production_id'] = all_key.name #生产单号
                    date_line['production_name'] = two_key.name #产成品名称
                    date_line['product_number'] = '%.4f'%(two_value['product_number']) #产成品数量
                    date_line['location_id'] = two_value['location_id'] #库位
                    date_line['analytic_plan'] = two_value['analytic_plan'] #辅助核算项
                    date_line['product_id'] = three_key.name #原料名称
                    date_line['inventory'] = '%.4f'%(three_value['inventory']) #投料数量
                    date_line['share_num'] = '%.4f'%(self.get_inventory_num(all_key.id,three_key.id)) #分摊数量
                    if float(date_line['inventory']) == 0:
                        date_line['share_num_actual'] = 0
                    else:
                        date_line['share_num_actual'] = float(date_line['share_num']) / float(date_line['inventory']) #分摊数量占投料数量的百分比
                    date_line['actual_consumption_num'] = '%.4f'%(float(date_line['inventory']) + float(date_line['share_num'])) #实际数量
                    date_line['actual_money'] = '%.4f'%((float(date_line['inventory']) + float(date_line['share_num'])) * three_value['price_unit']) #实际金额
                    if float(date_line['product_number']) == 0:
                        date_line['actual_price'] = '0.0000'
                    else:
                        date_line['actual_price'] = '%.4f'%(float(date_line['actual_money']) / float(date_line['product_number'])) #实际原料单份成本
                    date_line['theory_num'] = '%.4f'%(three_value['theory_num']) #理论数量
                    date_line['theory_money'] = '%.4f'%(float(date_line['theory_num']) * three_value['price_unit']) #理论金额
                    if float(date_line['product_number']) == 0:
                        date_line['theory_price'] = '0.0000'
                    else:
                        date_line['theory_price'] = '%.4f'%(float(date_line['theory_money']) / float(date_line['product_number'])) #理论原料单份成本
                    date_line['save_number'] = '%.4f'%(float(date_line['actual_consumption_num']) - float(date_line['theory_num'])) #节约数量
                    date_line['save_money'] = '%.4f'%(float(date_line['actual_money']) - float(date_line['theory_money'])) #节约金额
                    if float(date_line['product_number']) == 0:
                        date_line['average_number'] = '0.0000'
                        date_line['average_money'] = '0.0000'
                    else:
                        date_line['average_number'] = '%.4f'%(float(date_line['save_number']) / float(date_line['product_number'])) #平均每份数量
                        date_line['average_money'] = '%.4f'%(float(date_line['save_money']) / float(date_line['product_number'])) #平均每份金额
                    if float(date_line['theory_num']) == 0:
                        date_line['number_diff'] = '0.0000%'
                    else:
                        date_line['number_diff'] = '%.4f'%(float(date_line['save_number']) / float(date_line['theory_num']) * 100) + '%' #数量差异率
                    if float(date_line['theory_money']) == 0:
                       date_line['money_diff'] = '0.0000%'
                    else:
                        date_line['money_diff'] = '%.4f'%(float(date_line['save_money']) / float(date_line['theory_money']) * 100) + '%'#金额差异率
                    data.append(date_line)
        return data

    def __init__(self, cr, uid, name, context):
        self.start_date = context.get('start_date','')
        self.end_date = context.get('end_date','')
        self.analytic_plan = context.get('analytic_plan','')
        self.product_id = context.get('product_id','')
        self.mrp_production = context.get('mrp_production','')
        self.location_id = context.get('location_id','')
        super(qdodoo_mrp_actual_theory_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr': cr,
            'uid': uid,
            'employee': self.employee_get
        })

class report_accounts_receivable(osv.AbstractModel):
    _name = 'report.qdodoo_mrp_actual_theory_report.report_mrp_actual_theory'
    _inherit = 'report.abstract_report'
    _template = 'qdodoo_mrp_actual_theory_report.report_mrp_actual_theory'
    _wrapped_report_class = qdodoo_mrp_actual_theory_report
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
