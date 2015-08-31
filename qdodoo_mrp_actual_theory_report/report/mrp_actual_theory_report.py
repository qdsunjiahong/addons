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
    def employee_get(self):
        now_date = datetime.datetime.now().strftime('%Y-%m-%d ')
        data = []
        # 获取查询条件中的开始时间和结束时间
        start_date = self.start_date + ' 00:00:00'
        end_date = (self.end_date if self.end_date else now_date) + ' 23:59:59'
        sql = """select
                    mp.id as production_id,
                    mp.product_id as production_name,
                    sm.product_id as product_id,
                    sm.price_unit as actual_price,
                    sm.product_uom_qty as actual_consumption_num,
                    mp.product_qty as product_qty,
                    mppl.product_qty as theory_num,
                    mp.location_dest_id as location_id,
                    mp.analytic_account as analytic_account
                from mrp_production mp
                    LEFT JOIN stock_move sm ON sm.raw_material_production_id = mp.id
                    LEFT JOIN mrp_production_product_line mppl ON mppl.production_id = mp.id and mppl.product_id = sm.product_id
                where mp.state='done' and sm.product_uom_qty>0 and mp.date_planned >= '%s' and mp.date_planned <= '%s'
                """ % (start_date,end_date)
        if self.analytic_plan:
            sql += "and mp.analytic_account = '%s'"%self.analytic_plan
        if self.product_id:
            sql += "and mp.product_id = '%s'"%self.product_id
        if self.mrp_production:
            sql += "and mp.id = '%s'"%self.mrp_production
        if self.location_id[0][2]:
            sql += "and mp.location_dest_id in (%s)"%','.join([str(i) for i in self.location_id[0][2]])

        sql += """group by sm.id, mp.analytic_account, mp.date_planned, mp.product_qty, sm.product_id, mp.id, mp.state, sm.price_unit, sm.product_uom_qty,mppl.product_qty, mppl.product_id order by mp.id"""
        self.cr.execute(sql.decode('utf-8'))
        result = self.cr.fetchall()
        if not result:
            data = [{'start_date':self.start_date,'end_date':self.end_date if self.end_date else now_date,'production_name':'','production_id':'',
                     'product_id':'','actual_money':'','actual_consumption_num':'','actual_price':'','theory_num':'','theory_money':'','theory_price':'',
                     'save_number':'','save_money':'','average_number':'','average_money':''}]
            return data
        # 根据id获取库位名字
        dict_location = {}
        location_obj = self.pool.get('stock.location')
        location_ids = location_obj.search(self.cr,self.uid,['|',('active','=',1),('active','=',0)])
        for location_id in location_obj.browse(self.cr,self.uid,location_ids):
            dict_location[location_id.id] = location_id.complete_name.split('/',1)[1] if location_id.location_id else location_id.complete_name
        # 根据id获取辅助核算名字
        dict_analytic = {}
        analytic_obj = self.pool.get('account.analytic.account')
        analytic_ids = analytic_obj.search(self.cr,self.uid,[])
        for analytic_id in analytic_obj.browse(self.cr,self.uid,analytic_ids):
            dict_analytic[analytic_id.id] = analytic_id.name
        # 根据id获取产品名字
        dict_product = {}
        product_obj = self.pool.get('product.product')
        product_ids = product_obj.search(self.cr,self.uid,['|',('active','=',1),('active','=',0)])
        for product_id in product_obj.browse(self.cr,self.uid,product_ids):
            dict_product[product_id.id] = product_id.name
        # 根据id获取生产单名字
        dict_production = {}
        production_obj = self.pool.get('mrp.production')
        production_ids = production_obj.search(self.cr,self.uid,[])
        for production_id in production_obj.browse(self.cr,self.uid,production_ids):
            dict_production[production_id.id] = production_id.name
        # 循环所有查询出来的数据
        for production_id in result:
            production_num = production_id[6] if production_id[6] else 0.000
            val_dict = {}
            val_dict['save_money'] = '%.4f'%(production_id[3] * production_id[4] - production_num * (production_id[3] * production_id[4] / production_id[4])) #节约金额
            val_dict['average_money'] = '%.4f'%(float(val_dict['save_money']) / production_id[5]) #平均每份金额
            val_dict['save_number'] = '%.4f'%(production_id[4] - production_num)#节约数量
            val_dict['average_number'] = '%.4f'%(float(val_dict['save_number']) / production_id[5]) #平均每份数量
            val_dict['theory_price'] = '%.4f'%(production_num * (production_id[3] * production_id[4] / production_id[4])/production_id[5])#理论单价
            val_dict['theory_money'] = '%.4f'%(production_num * (production_id[3] * production_id[4] / production_id[4])) # 理论金额
            val_dict['theory_num'] = '%.4f'%(production_num) #理论数量
            val_dict['actual_price'] = '%.4f'%(production_id[3] * production_id[4] / production_id[5]) #实际单价
            val_dict['actual_consumption_num'] = '%.4f'%(production_id[4]) #实际数量
            val_dict['actual_money'] = '%.4f'%(production_id[3] * production_id[4]) #实际金额
            val_dict['product_id'] = dict_product.get(production_id[2],'')
            val_dict['production_name'] = dict_product.get(production_id[1],'')
            val_dict['production_id'] = dict_production.get(production_id[0],'')
            val_dict['location_id'] = dict_location.get(production_id[7],'')
            val_dict['analytic_plan'] = dict_analytic.get(production_id[8],'')
            val_dict['product_number'] = production_id[5]
            if production_num:
                val_dict['number_diff'] = '%.4f'%((production_id[4] - production_num)/production_num*100) + '%'
            else:
                val_dict['number_diff'] = 0.000
            if float(val_dict['theory_money']):
                val_dict['money_diff'] = '%.4f'%(float(val_dict['save_money'])/float(val_dict['theory_money'])*100) + '%'
            else:
                val_dict['money_diff'] = 0.000
            val_dict['start_date'] = self.start_date
            val_dict['end_date'] = self.end_date if self.end_date else now_date
            data.append(val_dict)
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

