# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:Qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
import datetime


class qdodoo_account_balance_search(models.TransientModel):
    """
        科目余额表条件查询试图
    """
    _name = 'qdodoo.account.balance.search'
    _description = 'qdodoo.account.balance.search'

    # 获取当前用户的公司id
    def _get_company_id(self):
        return self.env['res.users'].browse(self.env.uid).company_id.id

    start_p = fields.Many2one('account.period', string=u'开始期间', required=True)
    end_p = fields.Many2one('account.period', string=u'结束期间', required=True)
    company_id = fields.Many2one('res.company', string=u'公司', default=_get_company_id)

    @api.multi
    def btn_search(self):
        start_balance_dict = {}  # 科目期初{会计区间：{科目：{客户：期初}}}
        all_balance_dict = {}  # 科目期初{会计区间：{科目：期初}}
        line_balance_dict = {}  # 科目明细{会计区间：{科目：{客户：{借:,贷:,余额}}}}
        move_line_balance_dict = {}  # 科目明细{会计区间：{科目：{客户：{明细：{借:,贷:,余额}}}}}
        all_line_balance_dict = {} # 科目明细{会计区间：{科目：{借:,贷:}}}
        return_ids = [] #创建数据的id
        # 获取查询期间内的所有会计区间
        per_ids = self.env['account.period'].search([('company_id','=',self.company_id.id),('date_start', '>=', self.start_p.date_start), ('date_stop', '<=', self.end_p.date_stop)])
        for per_id in per_ids:
            # 查询每个会计区间的期初
            sql = """
            select
                l.partner_id as partner_id,
                l.account_id as account_id,
                (l.debit-l.credit) as balance,
                l.id as id
            from
                account_move_line l
                left join account_period p on (p.id=l.period_id)
            where
                p.date_stop < '%s' and l.company_id=%s
            group by l.partner_id,l.account_id,l.company_id,l.debit,l.credit,p.id,l.id
            """ % (per_id.date_start, per_id.company_id.id)
            self._cr.execute(sql)
            start_account_balance_dict = {} #科目期初{科目：{客户：期初}}
            all_balance_dict[per_id] = {}
            for balance_1 in self._cr.fetchall():
                # （客户、科目、余额、账期）
                partner_id, account_id, balance, line_id = balance_1

                # 如果没有业务伙伴，设置一个默认值
                if not partner_id:
                    partner_id = 'suifeng'
                if account_id in start_account_balance_dict:
                    start_account_balance_dict[account_id][partner_id] = start_account_balance_dict[account_id].get(partner_id,0.0) + balance
                    all_balance_dict[per_id][account_id] += balance
                else:
                    start_account_balance_dict[account_id] = {}
                    start_account_balance_dict[account_id][partner_id] = balance
                    all_balance_dict[per_id][account_id] = balance
            start_balance_dict[per_id] = start_account_balance_dict
            # 查询每个会计区间的数据
            sql1 = """
                select
                    l.partner_id as partner_id,
                    l.account_id as account_id,
                    l.debit as debit,
                    l.credit as credit,
                    (l.debit-l.credit) as balance,
                    l.move_id as move_id,
                    l.id as id
                from
                    account_move_line l
                where
                    l.state != 'draft' and l.period_id = %s
                group by
                    l.account_id, l.partner_id, l.debit, l.credit, l.id
            """% (per_id.id)
            self._cr.execute(sql1)
            line_account_balance_dict = {} #科目明细{科目：{客户：{借:,贷:,余额:}}}
            all_line_balance_dict[per_id] = {}
            move_line_balance_dict[per_id] = {}
            for balance_2 in self._cr.fetchall():
                partner_id, account_id, debit, credit, balance, move_id, line_id = balance_2
                # 如果没有业务伙伴，设置一个默认值
                if not partner_id:
                    partner_id = 'suifeng'
                if account_id in line_account_balance_dict:
                    if partner_id not in move_line_balance_dict[per_id][account_id]:
                        move_line_balance_dict[per_id][account_id][partner_id] = {}
                    move_line_balance_dict[per_id][account_id][partner_id][line_id] = {'debit':debit,'credit':credit,'balance':balance,'move_id':move_id}
                    all_line_balance_dict[per_id][account_id]['debit'] += debit
                    all_line_balance_dict[per_id][account_id]['credit'] += credit
                    all_line_balance_dict[per_id][account_id]['balance'] += balance
                    if line_account_balance_dict[account_id].get(partner_id):
                        line_account_balance_dict[account_id][partner_id]['debit'] += debit
                        line_account_balance_dict[account_id][partner_id]['credit'] += credit
                        line_account_balance_dict[account_id][partner_id]['balance'] += balance
                    else:
                        line_account_balance_dict[account_id][partner_id] = {'debit':debit,'credit':credit,'balance':balance}
                else:
                    line_account_balance_dict[account_id] = {}
                    line_account_balance_dict[account_id][partner_id] = {'debit':debit,'credit':credit,'balance':balance}
                    all_line_balance_dict[per_id][account_id] = {'debit':debit,'credit':credit,'balance':balance}
                    move_line_balance_dict[per_id][account_id] = {}
                    move_line_balance_dict[per_id][account_id][partner_id] = {}
                    move_line_balance_dict[per_id][account_id][partner_id][line_id] = {'debit':debit,'credit':credit,'balance':balance,'move_id':move_id}
            line_balance_dict[per_id] = line_account_balance_dict
        # 创建对应的数据
        for key,value in line_balance_dict.items():
            # (账期)
            for key1,value1 in value.items():
                # （科目）
                # 插入一级数据
                sql2 = """insert into qdodoo_account_balance (period_id,starting_balance,ending_balance,account_id,company_id,debit,credit) VALUES (%s,%s,%s,%s,%s,%s,%s) returning id""" % (
                    key.id, all_balance_dict[key].get(key1,0.0), all_balance_dict[key].get(key1,0.0)+all_line_balance_dict[key][key1]['balance'], key1, self.company_id.id,
                    all_line_balance_dict[key][key1]['debit'],all_line_balance_dict[key][key1]['credit'])
                self._cr.execute(sql2)
                account_periodly_id = self._cr.fetchall()[0][0]
                return_ids.append(account_periodly_id)
                for key2,value2 in value1.items():
                    # (客户，借.贷.余额)
                    # 将初始化的客户置为空
                    if key2 == 'suifeng':
                        partenr = 'Null'
                    else:
                        partenr = key2
                    start_balance = start_balance_dict[key][key1].get(key2,0.0) if start_balance_dict[key].get(key1) else 0.0
                    # 插入二级数据
                    sql3 = """insert into qdodoo_account_balance_partner (partner_id,account_periodly_id,period_id,account_id,company_id,debit,credit,start_balance,end_balance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id""" % (
                        partenr, account_periodly_id, key.id, key1, self.company_id.id, value2['debit'], value2['credit'],start_balance, start_balance+value2['balance'])
                    self._cr.execute(sql3)
                    report_id = self._cr.fetchall()[0][0]
                    for key3,value3 in move_line_balance_dict[key][key1][key2].items():
                        # 插入三级数据
                        sql4 = """insert into qdodoo_balance_partner_line (move_name,line_name,report_id,period_id,company_id,account_id,debit,credit) VALUES ('%s','%s',%s,%s,%s,%s,%s,%s)""" % (
                            value3.get('move_id'), key3, report_id, key.id, self.company_id.id, key1, value3.get('debit'), value3.get('credit'))
                        self._cr.execute(sql4)

        view_model, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_account_balance_sheet',
                                                                             'qdodoo_account_balance_report_tree')
        view_model2, view_id2 = self.env['ir.model.data'].get_object_reference('qdodoo_account_balance_sheet',
                                                                               'qdodoo_account_balance_report_form')
        search_model, search_id = self.env['ir.model.data'].get_object_reference('qdodoo_account_balance_sheet',
                                                                                 'qdodoo_account_balance_report_search')

        return {
            'name': (u'科目余额表'),
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'qdodoo.account.balance',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', return_ids)],
            'views': [(view_id, 'tree'), (view_id2, 'form')],
            'view_id': [view_id],
            'search_view_id': [search_id],
        }
