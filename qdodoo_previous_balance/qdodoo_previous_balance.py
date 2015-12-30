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

class qdodoo_account_date_month(models.Model):
    """
        每月保存科目余额表数据
    """
    _name = 'qdodoo.account.date.month'

    name = fields.Many2one('account.account',u'科目')
    period_id = fields.Many2one('account.period',u'会计区间')
    begin_money = fields.Float(u'期初余额')
    end_money = fields.Float(u'期末余额')
    debit = fields.Float(u'借方')
    credit = fields.Float(u'贷方')
    company_id = fields.Many2one('res.company',u'公司')
    partner_id = fields.Many2one('res.partner',u'业务伙伴')

    def get_date(self, cr, uid):
        move_line_obj = self.pool.get('account.move.line')
        period_obj = self.pool.get('account.period')
        # 获取上个月的会计区间(所有公司)
        date_now = datetime.now()
        period_date = date_now - timedelta(days=1)
        period_obj_ids = period_obj.search(cr, uid, [('date_start','<=',period_date),('date_stop','>=',period_date)])
        if period_obj_ids:
            # 获取所有区间的公司{公司:会计区间}--在此公司和会计区间是一一对应的
            period_company_dict = {}
            for line in period_obj.browse(cr, uid, period_obj_ids):
                period_company_dict[line.company_id.id] = line.id
            # 循环每个公司的分录明细
            # 组织数据字典{公司：{科目：{业务伙伴：{借方:''，贷方:''}}}}
            company_dict = {}
            for key,valus in period_company_dict.items():
                sql_1 = """select account_id,partner_id,debit,credit from account_move_line where period_id=%s and company_id=%s"""%(valus, key)
                cr.execute(sql_1)
                # 循环处理所有查询出来的数据
                company_account_dict = {}
                for move_line in cr.fetchall():
                    # 如果科目存在
                    if move_line[0] in company_account_dict:
                        if move_line[1]:
                            # 如果业务伙伴已存在（累加借方和贷方金额）
                            if move_line[1] in company_account_dict[move_line[0]]:
                                company_account_dict[move_line[0]][move_line[1]]['debit'] +=  move_line[2]
                                company_account_dict[move_line[0]][move_line[1]]['credit'] +=  move_line[3]
                            else:
                                company_account_dict[move_line[0]][move_line[1]] = {'debit':move_line[2],'credit':move_line[3]}
                        else:
                            # 业务伙伴为空
                            if 'tfs' in company_account_dict[move_line[0]]:
                                company_account_dict[move_line[0]]['tfs']['debit'] +=  move_line[2]
                                company_account_dict[move_line[0]]['tfs']['credit'] +=  move_line[3]
                            else:
                                company_account_dict[move_line[0]]['tfs'] = {'debit':move_line[2],'credit':move_line[3]}
                    else:
                        if move_line[1]:
                            # 科目不存在，计算业务伙伴数据
                            company_account_dict[move_line[0]] = {move_line[1]:{'debit':move_line[2],'credit':move_line[3]}}
                        else:
                            company_account_dict[move_line[0]] = {'tfs':{'debit':move_line[2],'credit':move_line[3]}}
                company_dict[key] = company_account_dict
            if company_dict:
                # {公司：{科目：{业务伙伴：{借方:''，贷方:''}}}}
                for key,valus in company_dict.items():
                    for key1,valus1 in valus.items():
                        begin_money = 0
                        end_money = 0
                        # 获取期初金额
                        sql_2 = """ select debit,credit,partner_id from account_move_line where period_id!=%s and company_id=%s and account_id=%s"""%(period_company_dict.get(key), key,key1)
                        cr.execute(sql_2)
                        # 获取{供应商:前期结余}
                        partner_money_dict = {}
                        for line_key in cr.fetchall():
                            # 如果客户有明细
                            partner = line_key[2] if line_key[2] else 'tfs'
                            if partner in partner_money_dict:
                                partner_money_dict[partner] += line_key[0] - line_key[1]
                            else:
                                partner_money_dict[partner] = line_key[0] - line_key[1]
                        for key_line,key_valus in partner_money_dict.items():
                            if key_line == 'tfs':
                                partner_id = 'Null'
                            else:
                                partner_id = key_line
                            if key_line in valus1:
                                debit = valus1[key_line].get('debit',0.0)
                                credit = valus1[key_line].get('credit',0.0)
                                end_money = key_valus + debit - credit
                            else:
                                debit = 0.0
                                credit = 0.0
                                end_money = key_valus
                            sql_3 = """ insert into qdodoo_account_date_month (name,period_id,begin_money,end_money,debit,credit,company_id,partner_id) values (%s,%s,%s,%s,%s,%s,%s,%s)"""%\
                                        (key1,period_company_dict.get(key),key_valus,end_money,debit,credit,key,partner_id)
                            cr.execute(sql_3)