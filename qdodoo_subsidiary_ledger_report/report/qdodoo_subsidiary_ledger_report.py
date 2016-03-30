# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import fields, osv
from openerp import tools
import time
from datetime import datetime,timedelta
from openerp.report import report_sxw
from openerp.tools.translate import _
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class qdodoo_subsidiary_ledger_report(report_sxw.rml_parse):
    # 根据内部调拨的id获取库存调拨单的名称
    def get_picking_name(self, move_id):
        move_obj = self.pool.get('stock.move')
        move_obj_obj = move_obj.browse(self.cr,self.uid,move_id)
        return move_obj_obj.picking_id and move_obj_obj.picking_id.name or ''
    def employee_get(self):
        now_date = datetime.now().strftime('%Y-%m-%d ')
        data = []
        # 获取查询条件中的开始时间和结束时间
        start_date = (datetime.strptime(self.start_date,'%Y-%m-%d') + timedelta(days=-1)).strftime('%Y-%m-%d') + ' 15:00:00'
        end_date = (self.end_date if self.end_date else now_date) + ' 15:59:59'
        sql = """select
                    sm.date as date,
                    sm.id as move_id,
                    sm.location_id as from_location_id,
                    sm.product_uom_qty as number
                from
                    stock_move sm
                where
                    sm.product_id = %s and (sm.location_dest_id = %s or sm.location_id = %s) and sm.state='done' and sm.date >= '%s' and sm.date <= '%s'
                """ % (self.product_id,self.location_id,self.location_id,start_date,end_date)
        sql += """group by sm.location_id,sm.product_id,sm.product_uom_qty,sm.date,sm.id order by sm.date"""
        self.cr.execute(sql.decode('utf-8'))
        result = self.cr.fetchall()
        # 根据id获取产品名字、编号
        dict_product = {}
        dict_product_num = {}
        product_obj = self.pool.get('product.product')
        product_ids = product_obj.search(self.cr,self.uid,['|',('active','=',1),('active','=',0)])
        for product_id in product_obj.browse(self.cr,self.uid,product_ids):
            dict_product[product_id.id] = product_id.name_template
            dict_product_num[product_id.id] = product_id.default_code
        # 根据id获取库位名字
        dict_location = {}
        location_obj = self.pool.get('stock.location')
        location_ids = location_obj.search(self.cr,self.uid,['|',('active','=',1),('active','=',0)])
        for location_id in location_obj.browse(self.cr,self.uid,location_ids):
            dict_location[location_id.id] = location_id.complete_name.split('/',1)[1] if location_id.location_id else location_id.complete_name
        if not result:
            data = [{'start_date':self.start_date,'end_date':self.end_date if self.end_date else now_date,'product_id':dict_product.get(self.product_id,''),'product_num':dict_product_num.get(self.product_id,''),
                     'location_id':dict_location.get(self.location_id,''),'date':'','move_id':'','description':'','debit_num':'','debit_money':'','credit_num':'',
                     'credit_money':'','balance_num':'','balance_money':''}]
            return data
        # 获取产品数据字典{id：采购价}
        product_cost = {}
        for line in product_obj.browse(self.cr, self.uid, product_obj.search(self.cr, self.uid, [])):
            product_cost[line.id] = line.standard_price
        # 获取昨天日期
        yesteday = datetime.strftime(datetime.strptime(self.start_date,'%Y-%m-%d') - timedelta(days=1),'%Y-%m-%d')
        # 该库位所有的产品和结余数量、金额
        product_num = {}
        banlance_obj = self.pool.get('qdodoo.previous.balance')
        for banlance_id in banlance_obj.browse(self.cr, self.uid, banlance_obj.search(self.cr, self.uid, [('location_id','=',self.location_id),('date','=',yesteday),('product_id','=',self.product_id)])):
            product_num['balance_num'] = product_id.balance_num
            product_num['balance_money'] = product_id.balance_money
        # 循环所有查询出来的数据
        data = [{'start_date':self.start_date,'end_date':self.end_date if self.end_date else now_date,'product_id':dict_product.get(self.product_id,''),'product_num':dict_product_num.get(self.product_id,''),
                     'location_id':dict_location.get(self.location_id,''),'date':yesteday,'move_id':0,'description':'前期结余','debit_num':product_num.get('balance_num',0.0000),'debit_money':product_num.get('balance_money',0.0000),'credit_num':0.0000,
                     'credit_money':0.0,'balance_num':product_num.get('balance_num',0.0000),'balance_money':product_num.get('balance_money',0.0000)}]
        for production_id in result:
            print production_id[3],'11111111111111'
            val_dict = {}
            credit_num = str(production_id[3] if self.location_id == production_id[2] else 0.0)
            val_dict['credit_num'] = credit_num[:credit_num.index('.')+5] #贷方数量
            credit_money = str(float(val_dict['credit_num']) * product_cost.get(self.product_id,0.0))
            val_dict['credit_money'] = credit_money[:credit_money.index('.')+5] # 贷方金额
            debit_num = str(production_id[3] if self.location_id != production_id[2] else 0.0)
            val_dict['debit_num'] = debit_num[:debit_num.index('.')+5] #借方数量
            debit_money = str(float(val_dict['debit_num']) * product_cost.get(self.product_id,0.0))
            val_dict['debit_money'] = debit_money[:debit_money.index('.')+5] #借方金额
            balance_money = str(product_num.get('balance_money',0.0) - float(val_dict['credit_money']) + float(val_dict['debit_money']))
            val_dict['balance_money'] = balance_money[:balance_money.index('.')+5] #结余金额
            product_num['balance_money'] = float(val_dict['balance_money'])
            balance_num = str(product_num.get('balance_num',0.0) - float(val_dict['credit_num']) + float(val_dict['debit_num']))
            val_dict['balance_num'] = balance_num[:balance_num.index('.')+5] #结余数量
            product_num['balance_num'] = float(val_dict['balance_num'])
            val_dict['description'] = ('从'+dict_location.get(production_id[2],'')+'发出') if self.location_id == production_id[2] else ('从'+dict_location.get(production_id[2],'')+'入库')
            val_dict['move_id'] = self.get_picking_name(production_id[1])
            val_dict['date'] = production_id[0]
            val_dict['location_id'] = dict_location.get(self.location_id,'') if self.location_id else '全部'
            val_dict['product_num'] = dict_product_num.get(self.product_id,'')
            val_dict['product_id'] = dict_product.get(self.product_id,'')
            val_dict['start_date'] = self.start_date
            val_dict['end_date'] = self.end_date if self.end_date else now_date
            data.append(val_dict)
        return data

    def __init__(self, cr, uid, name, context):
        self.start_date = context.get('start_date','')
        self.end_date = context.get('end_date','')
        self.product_id = context.get('product_id','')
        self.location_id = context.get('location_id','')
        super(qdodoo_subsidiary_ledger_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr': cr,
            'uid': uid,
            'employee': self.employee_get
        })

class report_accounts_receivable(osv.AbstractModel):
    _name = 'report.qdodoo_subsidiary_ledger_report.report_subsidiary_ledger'
    _inherit = 'report.abstract_report'
    _template = 'qdodoo_subsidiary_ledger_report.report_subsidiary_ledger'
    _wrapped_report_class = qdodoo_subsidiary_ledger_report
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
