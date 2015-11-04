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
            where l.state != 'draft'
            group by p.id, l.account_id, p.fiscalyear_id, p.date_start, am.company_id ,l.debit, l.credit
        """
        self.env.cr.execute(sql)
        key_list = []
        debit_dict = {}
        dict_line = {}
        credit_dict = {}
        data_start_dict = {}
        for line in self.env.cr.fetchall():
            if line[:4] in key_list:
                debit_dict[line[:4]] += line[4]
                credit_dict[line[:4]] += line[5]

            else:
                debit_dict[line[:4]] = line[4]
                credit_dict[line[:4]] = line[5]
                key_list.append(line[:4])
            data_start_dict[line[:4]] = line[7]
            line_data = self._return_result(line)
            line_value = dict_line.get(line[:4], [])
            line_value.append(line_data)
            dict_line[line[:4]] = line_value
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
                # 'periodly_lines': dict_line.get(key, False),
                'date': data_start_dict.get(key, False)
            }
            cre_obj = self.env['account.periodly'].create(data)
            # for key_line in dict_line.keys():
            value_line = dict_line.get(key, False)
            print value_line
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
