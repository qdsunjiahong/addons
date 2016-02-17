# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_account_move_wizard(models.Model):
    """
    批量打印wizard模型
    """
    _name = 'qdodoo.account.move.wizard'
    _description = 'qdodoo.account.move.wizard'

    def _get_company_id(self):
        return self.env.user.company_id.id

    start_date = fields.Date(string=u'开始时间')
    end_date = fields.Date(string=u'结束时间')
    company_id = fields.Many2one('res.company', string=u'公司', default=_get_company_id)
    journal_id = fields.Many2one('account.journal', string=u'账簿')

    # @api.multi
    def report_print(self, cr, uid, ids, context):
        context = context or {}
        data = self.browse(cr, uid, ids[0])
        report_obj = self.pool.get('qdodoo.account.move.report')
        sql_del1 = """delete from account_move_report_line where 1=1"""
        cr.execute(sql_del1)
        sql_del2 = """delete from qdodoo_account_move_report where 1=1"""
        cr.execute(sql_del2)
        report_list = []
        company_name = data.company_id.name
        create_user = self.pool.get('res.users').browse(cr, uid, uid).name

        account_debit = {}  # 借方金额{"account_name":debit}
        account_credit = {}  # 贷方金额{"account_name":credit}
        report_ids = []
        sql_search = """
        select
            aml.id as id,
            aml.name as aml_name,
            aml.debit as debit,
            aml.credit as credit,
            aa.name as account_name,
            rp.name as partner_name,
            am.name as am_name
        from account_move_line aml
          left join account_move am on am.id=aml.move_id
          left join account_account aa on aa.id=aml.account_id
          left join res_partner rp on rp.id = aml.partner_id
        where am.state = 'posted' and am.date >= '%s' and am.date <= '%s' and am.company_id = %s and am.journal_id= %s
        group by
            aml.id,aml.name,aml.debit,aml.credit,aa.name,rp.name,am.name
        """ % (data.start_date, data.end_date, data.company_id.id, data.journal_id.id)
        cr.execute(sql_search)
        result = cr.fetchall()
        min_n = 0
        min_number = ''
        max_n = 0
        max_number = ''
        for res in result:
            aml_id, aml_name, debit, credit, account_name, partner_name, am_name = res
            am_number = am_name.split("/")[-1]
            if min_n == 0 and max_n == 0:
                min_n = int(am_number)
                max_n = int(am_number)
                min_number = am_name
                max_number = am_name
            else:
                if int(am_number) > max_n:
                    max_number = am_name
                if int(am_number) < min_n:
                    min_number = am_name
            if partner_name:
                account_name = account_name + '/' + partner_name
            account_debit[account_name] = account_debit.get(account_name, 0) + debit
            account_credit[account_name] = account_credit.get(account_name, 0) + credit
            if account_name not in report_list:
                report_list.append(account_name)
        report_line_list = []
        for report_l in report_list:
            debit = account_debit.get(report_l, 0)
            credit = account_credit.get(report_l, 0)
            data = {
                'account_name': report_l,
                'debit': debit,
                'credit': credit
            }
            report_line_list.append((0, 0, data))
        date = fields.Date.today()
        report_line_list_new = []
        for report_line_l in report_line_list:
            report_line_list_new.append(report_line_l)
            if len(report_line_list_new) % 5 == 0:
                data_p = {
                    'min_number': min_number,
                    'max_number': max_number,
                    'date': date,
                    'company_name': company_name,
                    'create_user': create_user,
                    'report_lines': report_line_list_new,
                }
                create_id1 = report_obj.create(cr, uid, data_p)
                report_ids.append(create_id1)
                report_line_list_new = []
        if len(report_line_list_new) > 0:
            data_p = {
                'min_number': min_number,
                'max_number': max_number,
                'date': date,
                'company_name': company_name,
                'create_user': create_user,
                'report_lines': report_line_list_new,
            }
            create_id1 = report_obj.create(cr, uid, data_p)
            report_ids.append(create_id1)

        context['active_ids'] = [report_ids]
        context['active_model'] = 'qdodoo.account.move.report'
        return self.pool.get("report").get_action(cr, uid, [],
                                           'qdodoo_account_move_report.qdodoo_account_move_report2',
                                           context=context)


class qdodoo_account_move_report(models.Model):
    """
    凭证打印整合模块
    """
    _name = 'qdodoo.account.move.report'
    _description = 'qdodoo.account.move.report'

    date = fields.Date(string=u'日期')
    min_number = fields.Char(string=u'最小凭证号')
    max_number = fields.Char(string=u'最大凭证号')
    company_name = fields.Char(string=u'核算单位')
    create_user = fields.Char(string=u'制单人')
    report_lines = fields.One2many('account.move.report.line', 'report_id')


class account_move_report_line(models.Model):
    """
    明细
    """
    _name = 'account.move.report.line'
    _description = 'account.move.report.line'

    report_id = fields.Many2one('qdodoo.account.move.report')
    name = fields.Char(string=u'名称')
    account_name = fields.Char(string=u'科目')
    debit = fields.Float(string=u'借方金额')
    credit = fields.Float(string=u'贷方金额')

class qdodoo_account_account_tfs(models.Model):
    _inherit = 'account.account'

    all_name = fields.Char(u'全名',compute="_get_all_name")

    def _get_all_name(self):
        for ids in self:
            ids.all_name = ids.name
            acc = ids
            while acc.parent_id:
                ids.all_name = acc.parent_id.name +' / '+ ids.all_name
                acc = acc.parent_id

