# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_partner_payment_wizard(models.Model):
    """
    供应商账务动态表查询wizard视图
    """
    _name = 'qdodoo.partner.payment.wizard'
    _description = 'qdodoo.partner.payment.wizard'

    year = fields.Many2one('account.fiscalyear', string=u'年度')
    month = fields.Selection((('01', u'一月'), ('02', u'二月'), ('03', u'三月'), ('04', u'四月'),
                              ('05', u'五月'), ('06', u'六月'), ('07', u'七月'), ('08', u'八月'), ('09', u'九月'),
                              ('10', u'十月'), ('11', u'十一月'), ('12', u'十二月')), string=u'月份')
    partner_ids = fields.Many2many('res.partner', 'partner_payment_rel', 'payment_id', 'partner_id', string=u'供应商')
    date = fields.Date(string=u'日期')

    @api.multi
    def action_done(self):
        year_name = self.year.name
        month = self.month
        date = self.date
        partner_ids=self.partner_ids
        if not year_name and not month and not date:
            raise except_orm(_(u'警告'), _(u'查询条件不能为空'))
        report_obj = self.env['qdodoo.partner.payment.report']
        unlink_ids = report_obj.search([])
        unlink_ids.unlink()
        fiscalyear_obj = self.env['account.fiscalyear']
        period_obj = self.env['account.period']
        model_obj = self.env['ir.model.data']
        result_list = []
        date_char = ''
        partner_list_res = []
        partner_amount_total = {}
        partner_residual = {}
        sql = """
            select
                ai.partner_id as partner_id,
                ai.amount_total as amount_total,
                ai.residual as residual
            from account_invoice ai
                LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ai.id
                LEFT JOIN purchase_order po ON po.id = pir.purchase_id
            where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
            """
        sql_domain = []
        if year_name and month:
            month_ids = period_obj.search([('name', '=', str(month) + "/" + year_name)])
            if month_ids:
                sql_domain = sql_domain + [month_ids[0].date_start + " 00:00:01", month_ids[0].date_stop + " 23:59:59"]
                date_char = str(month) + '/' + year_name
        elif year_name and not month:
            year_ids = fiscalyear_obj.search([('name', '=', year_name)])
            if year_ids:
                sql_domain = sql_domain + [year_ids[0].date_start + " 00:00:01", year_ids[0].date_stop + " 23:59:59"]
                date_char = year_name
        if date:
            sql_domain = sql_domain + [date + " 00:00:01", date + " 23:59:59"]
            date_char = date
        if self.partner_ids:
            partner_list = []
            for partner_id in partner_ids:
                partner_list.append(partner_id.id)
            if len(partner_list) == 1:
                sql = sql + " and po.partner_id = %s"
                sql_domain.append(partner_list[0])
            else:
                sql = sql + " and po.partner_id in %s"
                sql_domain.append(tuple(partner_list))
        sql = sql % tuple(sql_domain)
        self.env.cr.execute(sql)
        res = self.env.cr.fetchall()
        if res:
            for res_line in res:
                key_l = res_line[0]
                if key_l in partner_list_res:
                    partner_amount_total[key_l] += res_line[1]
                    partner_residual[key_l] += res_line[2]
                else:
                    partner_amount_total[key_l] = res_line[1]
                    partner_residual[key_l] = res_line[2]
                    partner_list_res.append(key_l)
            if partner_list_res:
                for partner_l in partner_list_res:
                    data = {
                        'partner_id': partner_l,
                        'date': date_char,
                        'amount': partner_amount_total.get(partner_l, 0),
                        'paid_amount': partner_amount_total.get(partner_l, 0) - partner_residual.get(partner_l, 0),
                        'unpaid_amount': partner_residual.get(partner_l, 0)
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                vie_model, view_id = model_obj.get_object_reference('qdodoo_partner_payment',
                                                                    'qdodoo_partner_payment_report_tree')
                view_model, search_id = model_obj.get_object_reference('qdodoo_partner_payment',
                                                                       'qdodoo_partner_payment_report_search')
                return {
                    'name': _('供应商账务动态表'),
                    'view_type': 'form',
                    "view_mode": 'tree',
                    'res_model': 'qdodoo.partner.payment.report',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', result_list)],
                    'views': [(view_id, 'tree')],
                    'view_id': [view_id],
                    'search_view_id': [search_id]
                }
        else:
            raise except_orm(_(u'提示'), _(u'未查询到数据'))
