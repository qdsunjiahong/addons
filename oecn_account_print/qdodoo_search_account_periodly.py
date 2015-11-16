# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _


class account_periodly_search(models.Model):
    _name = 'account.periodly.search'

    # @api.multi
    def _get_company_id(self):
        return self.env['res.users'].browse(self.env.uid).company_id.id

    start_p = fields.Many2one('account.period', string=u'开始期间', required=True)
    end_p = fields.Many2one('account.period', string=u'结束期间', required=True)
    company_id = fields.Many2one('res.company', string=u'公司', default=_get_company_id)

    @api.multi
    def btn_search(self):
        periodly_obj = self.env['account.periodly']
        periodly_obj.search([]).unlink()
        per_list = []
        per_ids = self.env['account.period'].search(
            [('date_start', '>=', self.start_p.date_start), ('date_stop', '<=', self.end_p.date_stop)])
        for per_id in per_ids:
            per_list.append(per_id.id)
        sql = """
            select
                l.id as l_id,
                l.period_id as period_id,
                l.account_id as account_id,
                am.company_id as company_id,
                l.debit as debit,
                l.credit as credit,
                (l.debit-l.credit) as balance,
                l.date as date,
                l.name as line_name,
                am.name as move_name
            from
                account_move_line l
                left join account_account a on (a.id=l.account_id)
                left join account_move am on (am.id=l.move_id)
            where l.state != 'draft' and l.period_id in %s
            group by l.name,am.name, l.period_id, l.account_id, am.company_id ,l.debit, l.credit,l.id
        """ % (tuple(per_list),)
        self.env.cr.execute(sql)
        key_list = []
        debit_dict = {}
        dict_line = {}
        credit_dict = {}
        data_start_dict = {}
        for line in self.env.cr.fetchall():
            k_l = line[1:4]
            if k_l in key_list:
                debit_dict[k_l] += line[4]
                credit_dict[k_l] += line[5]
                dict_line[k_l] += [(line[2], line[4], line[5], line[-2], line[-1])]

            else:
                debit_dict[k_l] = line[4]
                credit_dict[k_l] = line[5]
                dict_line[k_l] = [(line[2], line[4], line[5], line[-2], line[-1])]
                key_list.append(k_l)
            data_start_dict[k_l] = line[7]
        return_ids = []
        for key in key_list:
            # 获取账期开始时间

            # 获取期初
            sql3 = """
            select
                sum(l.debit-l.credit) as balance
            from
                account_move_line l
                left join account_period p on (l.period_id=p.id)
            where
                p.date_start < '%s' and l.account_id = %s and l.company_id = %s
            """ % (self.start_p.date_start, key[1], key[2])
            self.env.cr.execute(sql3)
            res = self.env.cr.fetchall()
            starting_balance = 0.0
            if res[0][0]:
                starting_balance = res[0][0]
            data = {
                'period_id': key[0],
                'starting_balance': starting_balance,
                'ending_balance': starting_balance + debit_dict.get(key, 0) - credit_dict.get(key, 0),
                'account_id': key[1],
                'company_id': key[2],
                'debit': debit_dict.get(key, 0),
                'credit': credit_dict.get(key, 0),
                'balance': debit_dict.get(key, 0) - credit_dict.get(key, 0),
                'date': data_start_dict.get(key, False)
            }
            cre_obj = periodly_obj.create(data)
            value_line = dict_line.get(key, False)
            if value_line:
                for v in value_line:
                    sql_lines = """
                          insert into account_periodly_line (move_name,line_name,account_id,debit,credit,account_periodly_id) VALUES ('%s','%s',%s,%s,%s,%s)
                        """ % (v[-1], v[-2], v[0], v[1], v[2], cre_obj.id)
                    self.env.cr.execute(sql_lines)
            return_ids.append(cre_obj.id)
        view_model, view_id = self.env['ir.model.data'].get_object_reference('oecn_account_print',
                                                                             'view_account_periodly_tree')
        view_model2, view_id2 = self.env['ir.model.data'].get_object_reference('oecn_account_print',
                                                                               'view_account_periodly_form')

        return {
            'name': (u'科目余额表'),
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'account.periodly',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', return_ids)],
            'views': [(view_id, 'tree'), (view_id2, 'form')],
            'view_id': [view_id],
        }

    def _return_result(self, args):
        data = [args[2], args[4], args[5]]
        return data
