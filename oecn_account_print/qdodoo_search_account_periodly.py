# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
import datetime


class account_periodly_search(models.Model):
    _name = 'account.periodly.search'

    def _get_company_id(self):
        return self.env['res.users'].browse(self.env.uid).company_id.id

    start_p = fields.Many2one('account.period', string=u'开始期间', required=True)
    end_p = fields.Many2one('account.period', string=u'结束期间', required=True)
    company_id = fields.Many2one('res.company', string=u'公司', default=_get_company_id)

    @api.multi
    def btn_search(self):
        sql_del1 = """delete from qdodoo_account_partner_line where 1=1"""
        self.env.cr.execute(sql_del1)
        sql_del2 = """delete from qdodoo_account_partner_report where 1=1"""
        self.env.cr.execute(sql_del2)
        sql_del3 = """delete from account_periodly where 1=1"""
        self.env.cr.execute(sql_del3)
        per_list = []
        starting_balance_dict = {}  # 科目期初
        start_partner_dict = {}  # 客户期初
        account_list = []  # 起初科目
        per_ids = self.env['account.period'].search(
            [('date_start', '>=', self.start_p.date_start), ('date_stop', '<=', self.end_p.date_stop)])
        # 查询出所有的会计区间
        for per_id in per_ids:
            per_list.append(per_id.id)
            # 查询每个会计的区间起初
            sql3 = """
            select
                l.partner_id as partner_id,
                l.account_id as account_id,
                l.company_id as company_id,
                (l.debit-l.credit) as balance
            from
                account_move_line l
                left join account_period p on (l.period_id=p.id)
            where
                p.date_start < '%s' and l.company_id=%s
            group by l.partner_id,l.account_id,l.company_id,l.debit,l.credit
            """ % (per_id.date_start, per_id.company_id.id)
            self.env.cr.execute(sql3)
            res_balance = self.env.cr.fetchall()
            if res_balance:
                for balance_l in res_balance:
                    # （会计区间id，科目，公司）
                    key_balance = (per_id.id, balance_l[1], balance_l[2])
                    # （客户，会计区间，科目，公司）
                    key_balance_partner = (balance_l[0], per_id.id, balance_l[1], balance_l[2])
                    # {（会计区间id，科目，公司）:余额}
                    starting_balance_dict[key_balance] = starting_balance_dict.get(key_balance, 0) + balance_l[3]
                    # {（客户，会计区间，科目，公司）:余额}
                    start_partner_dict[key_balance_partner] = start_partner_dict.get(key_balance_partner, 0) + \
                                                              balance_l[3]
                    if key_balance_partner not in account_list:
                        account_list.append(key_balance_partner)
        sql = ''
        if per_list and len(per_list) == 1:
            sql = """
                select
                    l.partner_id as partner_id,
                    l.period_id as period_id,
                    l.account_id as account_id,
                    l.company_id as company_id,
                    l.debit as debit,
                    l.credit as credit,
                    (l.debit-l.credit) as balance,
                    l.name as line_name,
                    am.name as move_name
                from
                    account_move_line l
                    left join account_account a on (a.id=l.account_id)
                    left join account_move am on (am.id=l.move_id)
                where l.state != 'draft' and l.period_id = %s
                group by l.name,am.name, l.period_id, l.account_id, l.company_id ,l.debit, l.credit,l.id
            """ % per_list[0]
        elif per_list and len(per_list) > 1:
            sql = """
                select
                    l.partner_id as partner_id,
                    l.period_id as period_id,
                    l.account_id as account_id,
                    l.company_id as company_id,
                    l.debit as debit,
                    l.credit as credit,
                    (l.debit-l.credit) as balance,
                    l.name as line_name,
                    am.name as move_name
                from account_move_line l
                    left join res_partner rp on rp.id = l.partner_id
                    left join account_move am on (am.id=l.move_id)
                where l.state != 'draft' and l.period_id in %s
                group by l.name,am.name, l.period_id, l.account_id, l.company_id ,l.debit, l.credit,l.id
            """ % (tuple(per_list),)
        self.env.cr.execute(sql)
        key_list = []  # 总计
        debit_dict = {}
        credit_dict = {}
        # 每个客户的借贷
        partner_key_list = []
        partner_dict_credit = {}
        partner_dict_debit = {}
        partner_line_dict = {}
        # 最后循环列表
        for_list = []
        for_dict = {}
        for line in self.env.cr.fetchall():
            k_l = line[1:4]
            partner_key = line[:4]  # 客户键值
            if k_l in key_list:
                debit_dict[k_l] += line[4]
                credit_dict[k_l] += line[5]
            else:
                debit_dict[k_l] = line[4]
                credit_dict[k_l] = line[5]
                key_list.append(k_l)
            if partner_key in partner_key_list:
                partner_dict_credit[partner_key] += line[5]
                partner_dict_debit[partner_key] += line[4]
                partner_line_dict[partner_key] += [(line[4], line[5], line[6], line[7], line[8])]
            else:
                partner_dict_credit[partner_key] = line[5]
                partner_dict_debit[partner_key] = line[4]
                partner_line_dict[partner_key] = [(line[4], line[5], line[6], line[7], line[8])]
                partner_key_list.append(partner_key)
        return_ids = []
        for key in list(set(partner_key_list + account_list)):
            if key[1:] not in for_list:
                ending_balance = starting_balance_dict.get(key[1:], 0) + debit_dict.get(key[1:], 0) - credit_dict.get(
                    key[1:], 0)
                balance = debit_dict.get(key[1:], 0) - credit_dict.get(key[1:], 0)
                sql_1 = """
                insert into account_periodly (period_id,starting_balance,ending_balance,account_id,company_id,debit,credit,balance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) returning id
                """ % (key[1], starting_balance_dict.get(key[1:], 0), ending_balance, key[2], key[3],
                       debit_dict.get(key[1:], 0),
                       credit_dict.get(key[1:], 0), balance)
                self.env.cr.execute(sql_1)
                sql_result1 = self.env.cr.fetchall()
                for_dict[key[1:]] = sql_result1[0][0]
                for_list.append(key[1:])
                return_ids.append(sql_result1[0][0])
            starting_balance_partner = start_partner_dict.get(key, 0)
            ending_balance_partner = start_partner_dict.get(key, 0) + partner_dict_debit.get(key,
                                                                                             0) - partner_dict_credit.get(
                key, 0)

            if key[0]:
                sql_2 = """
                insert into qdodoo_account_partner_report (account_periodly_id,partner_id,period_id,account_id,company_id,debit,credit,start_balance,end_balance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id
                """ % (
                    for_dict.get(key[1:]), key[0], key[1], key[2], key[3], partner_dict_debit.get(key, 0),
                    partner_dict_credit.get(key, 0), starting_balance_partner, ending_balance_partner)
            else:
                sql_2 = """
                insert into qdodoo_account_partner_report (account_periodly_id,period_id,account_id,company_id,debit,credit,start_balance,end_balance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) returning id
                """ % (
                    for_dict.get(key[1:]), key[1], key[2], key[3], partner_dict_debit.get(key, 0),
                    partner_dict_credit.get(key, 0), starting_balance_partner, ending_balance_partner)
            self.env.cr.execute(sql_2)
            sql_result2 = self.env.cr.fetchall()
            if partner_line_dict.get(key, False):
                for par_l in partner_line_dict.get(key):
                    sql_line = """
                    insert into qdodoo_account_partner_line (move_name,line_name,report_id,period_id,company_id,account_id,debit,credit) VALUES ('%s','%s',%s,%s,%s,%s,%s,%s)
                    """ % (par_l[4], par_l[3], sql_result2[0][0], key[1], key[3], key[2], par_l[0], par_l[1])
                    self.env.cr.execute(sql_line)
        view_model, view_id = self.env['ir.model.data'].get_object_reference('oecn_account_print',
                                                                             'view_account_periodly_tree')
        view_model2, view_id2 = self.env['ir.model.data'].get_object_reference('oecn_account_print',
                                                                               'view_account_periodly_form')
        search_model, search_id = self.env['ir.model.data'].get_object_reference('oecn_account_print',
                                                                                 'view_account_periodly_search')

        return {
            'name': (u'科目余额表'),
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'account.periodly',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', return_ids)],
            'views': [(view_id, 'tree'), (view_id2, 'form')],
            'view_id': [view_id],
            'search_view_id': [search_id],
        }


class qdodoo_account_partner_report(models.Model):
    _name = 'qdodoo.account.partner.report'
    _description = 'qdodoo.account.partner.report'
    _rec_name = 'partner_id'

    account_periodly_id = fields.Many2one('account.periodly', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string=u'业务伙伴', readonly=True)
    period_id = fields.Many2one('account.period', string=u'期间', readonly=True)
    company_id = fields.Many2one('res.company', string=u'公司', readonly=True)
    start_balance = fields.Float(string=u'期初', readonly=True)
    debit = fields.Float(string=u'借方', readonly=True)
    credit = fields.Float(string=u'贷方', readonly=True)
    end_balance = fields.Float(string=u'期末', readonly=True)
    account_id = fields.Many2one('account.account', string=u'科目', readonly=True)
    line_ids = fields.One2many('qdodoo.account.partner.line', 'report_id', string=u'明细')


class qdodoo_account_partner_line(models.Model):
    _name = 'qdodoo.account.partner.line'
    _description = 'qdodoo.account.partner.line'

    report_id = fields.Many2one('qdodoo.account.partner.report', string=u'业务伙伴', readonly=True, ondelete='cascade')
    period_id = fields.Many2one('account.period', string=u'期间', readonly=True)
    company_id = fields.Many2one('res.company', string=u'公司', readonly=True)
    debit = fields.Float(string=u'借方', readonly=True)
    credit = fields.Float(string=u'贷方', readonly=True)
    account_id = fields.Many2one('account.account', string=u'科目', readonly=True)
    move_name = fields.Char(string=u'凭证号', readonly=True)
    line_name = fields.Char(string=u'名称', readonly=True)
