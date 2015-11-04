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

    start_p = fields.Many2one('account.period', string=u'开始期间')
    end_p = fields.Many2one('account.period', string=u'结束期间')
    company_id = fields.Many2one('res.company', string=u'公司', default=_get_company_id)

    @api.multi
    def btn_search(self):
        sql = """
            select
                p.fiscalyear_id as fiscalyear_id,
                p.id as period_id,
                l.account_id as account_id,
                am.company_id as company_id,
                l.debit as debit,
                l.credit as credit,
                (l.debit-l.credit) as balance,
                p.date_start as date
            from
                account_move_line l
                left join account_account a on (l.account_id = a.id)
                left join account_move am on (am.id=l.move_id)
                left join account_period p on (am.period_id=p.id)
            where l.state != 'draft' and l.date >= '%s' and l.date <= '%s' and l.company_id = %s
            group by p.id, l.account_id, p.fiscalyear_id, p.date_start, am.company_id ,l.debit, l.credit
        """ % (self.start_p.date_start, self.end_p.date_stop,self.company_id.id)
        self.env.cr.execute(sql)
        key_list = []
        debit_dict = {}
        dict_line = {}
        credit_dict = {}
        data_start_dict = {}
        for line in self.env.cr.fetchall():
            k_l = line[:4]
            if line[:4] in key_list:
                debit_dict[k_l] += line[4]
                credit_dict[k_l] += line[5]
                dict_line[k_l] += [(line[2], line[4], line[5])]

            else:
                debit_dict[k_l] = line[4]
                credit_dict[k_l] = line[5]
                dict_line[k_l] = [(line[2], line[4], line[5])]
                key_list.append(k_l)
            data_start_dict[k_l] = line[7]
        return_ids = []
        for key in key_list:
            data = {
                'fiscalyear_id': key[0],
                'period_id': key[1],
                'account_id': key[2],
                'company_id': key[3],
                'debit': debit_dict.get(key, 0),
                'credit': credit_dict.get(key, 0),
                'balance': debit_dict.get(key, 0) - credit_dict.get(key, 0),
                'date': data_start_dict.get(key, False)
            }
            cre_obj = self.env['account.periodly'].create(data)
            value_line = dict_line.get(key, False)
            if value_line:
                for v in value_line:
                    sql_lines = """
                          insert into account_periodly_line (account_id,debit,credit,account_periodly_id) VALUES (%s,%s,%s,%s)
                        """ % (v[0], v[1], v[2], cre_obj.id)
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
