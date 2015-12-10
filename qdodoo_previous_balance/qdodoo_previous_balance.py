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
        users_obj = self.pool.get('res.users')
        company_obj = self.pool.get('res.company')
        location_dict = {}
        date = datetime.now().date()
        # 获取每个公司的第一个员工
        company_person_dict = {}
        for company_id in company_obj.search(cr, uid, []):
            users_ids = users_obj.search(cr, uid, [('company_id','=',company_id)])
            if users_ids:
                company_person_dict[company_id] = users_ids[0]
        # 获取每个产品对应的公司id
        company_product_dict = {}
        product_ids = product_id.search(cr, uid, [])
        for product_id_new in product_id.browse(cr, uid, product_ids):
            if product_id_new.company_id.id in company_product_dict:
                company_product_dict[product_id_new.company_id.id].append(product_id_new.id)
            else:
                company_product_dict[product_id_new.company_id.id] = [product_id_new.id]
        # 获取产品数据字典{id：采购价}
        product_cost = {}
        for line,line_vlaue in company_product_dict.items():
            for lines in product_id.browse(cr,company_person_dict.get(line,1),line_vlaue):
                product_cost[lines.id] = lines.standard_price
        # 循环所有的库位
        for location in stock_id.search(cr, uid, []):
            quant_ids = []
            product_dict = {}
            # 从份中获取指定库位的数据
            # 查询对应库位的份
            sql1 = """ select product_id,qty from stock_quant where location_id=%s """%location
            cr.execute(sql1)
            for all_line in cr.fetchall():
                if all_line[0] in product_dict:
                    product_dict[all_line[0]] += all_line[1]
                else:
                    product_dict[all_line[0]] = all_line[1]
            location_dict[location] = product_dict
        for location_id in location_dict:
            for product_id,value in location_dict[location_id].items():
                sql = """ insert into qdodoo_previous_balance (location_id,product_id,date,balance_num,balance_money) values (%s,%s,'%s',%s,%s)"""%(location_id,product_id,str(date),value,value*product_cost.get(product_id,0.0))
                cr.execute(sql)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: