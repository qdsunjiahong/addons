# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_sale_chart_p(models.Model):
    _name = 'qdodoo.sale.chart.report.p'

    partner_id = fields.Many2one('res.partner', string=u'客户')
    section_id = fields.Many2one('crm.case.section', string=u'销售团队/品牌')
    sale_cost = fields.Float(digits=(16, 4), string=u'销售成本')
    sales_revenue = fields.Float(digits=(16, 4), string=u'销售收入')
    sale_chart = fields.Float(digits=(16, 4), string=u'销售毛利')
    gross_profit_margin = fields.Char(string=u'销售毛利率')


class qdodoo_search_sale_chart_p(models.Model):
    _name = 'qdodoo.search.sale.chart.p'
    date_start = fields.Date(string=u'开始时间', required=True)
    date_end = fields.Date(string=u'结束时间')

    @api.multi
    def btn_search(self):
        user_obj = self.env['res.users'].browse(self.env.uid)
        company_id = user_obj.company_id.id
        company_name = user_obj.company_id.name
        view_ids = self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company_id)])
        if len(view_ids) == 1:
            view_id = view_ids.id
        elif len(view_ids) > 1:
            raise except_orm(_(u'警告'), _(u'查询到%s有多个销售账簿') % (company_name))
        elif not view_ids:
            raise except_orm(_(u'警告'), _(u'%s未创建销售账簿') % (company_name))
        view_model, view_id2 = self.env['ir.model.data'].get_object_reference('qdodoo_sale_chart_report_p',
                                                                              'qdodoo_sale_chart_report_p')
        if self.date_end:
            invoice_ids = self.env['account.invoice'].search(
                [('date_invoice', '<=', self.date_end), ('type', '=', 'out_invoice'),
                 ('date_invoice', '>=', self.date_start), ('state', '=', 'paid'),
                 ('journal_id', '=', view_id)])
        else:
            invoice_ids = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice'),
                 ('date_invoice', '>=', self.date_start), ('state', '=', 'paid'),
                 ('journal_id', '=', view_id)])
        if invoice_ids:
            sale_list = []
            cost_dict = {}
            income_dict = {}
            sale_list2 = []
            result_list = []
            for invoice_id in invoice_ids:
                sql = """
                    select
                        soil.order_id
                    from
                        sale_order_invoice_rel soil
                    WHERE
                        soil.invoice_id = %s
                    """ % invoice_id.id
                self.env.cr.execute(sql)
                result = self.env.cr.fetchall()
                if result:
                    sale = self.env['sale.order'].browse(result[0][0])
                    if sale.procurement_group_id:
                        picking_ids = self.env['stock.picking'].search(
                            [('group_id', '=', sale.procurement_group_id.id), ('state', '=', 'done')])

                for picking_id in picking_ids:
                    a_move_lines = self.env['account.move.line'].search(
                        [('ref', '=', picking_id.name), ('debit', '>', 0)])
                    a_move_lines2 = self.env['account.move.line'].search(
                        [('ref', '=', invoice_id.number), ('credit', '>', 0)])
                    if a_move_lines:
                        for a_move_line in a_move_lines:
                            if (a_move_line.partner_id.id, sale.section_id.id) in sale_list:
                                cost_dict[(a_move_line.partner_id.id, sale.section_id.id)] += a_move_line.debit
                            else:
                                cost_dict[(a_move_line.partner_id.id, sale.section_id.id)] = a_move_line.debit
                                sale_list.append((a_move_line.partner_id.id, sale.section_id.id))
                    if a_move_lines2:
                        for a_move_line2 in a_move_lines2:
                            if (a_move_line2.partner_id.id, sale.section_id.id) in sale_list2:
                                income_dict[(a_move_line2.partner_id.id, sale.section_id.id)] += a_move_line2.credit
                            else:
                                income_dict[(a_move_line2.partner_id.id, sale.section_id.id)] = a_move_line2.credit
                                sale_list2.append((a_move_line2.partner_id.id, sale.section_id.id))
            sale_list_new = list(set(sale_list2 + sale_list))
            for sale_list_l in sale_list_new:
                if income_dict.get(sale_list_l, 0) == 0:
                    data = {
                        'partner_id': sale_list_l[0],
                        'section_id': sale_list_l[1],
                        'sale_cost': cost_dict.get(sale_list_l, 0),
                        'sales_revenue': income_dict.get(sale_list_l, 0),
                        'sale_chart': income_dict.get(sale_list_l, 0) - cost_dict.get(sale_list_l, 0),
                        'gross_profit_margin': '0%',
                    }
                else:
                    data = {
                        'partner_id': sale_list_l[0],
                        'section_id': sale_list_l[1],
                        'sale_cost': cost_dict.get(sale_list_l, 0),
                        'sales_revenue': income_dict.get(sale_list_l, 0),
                        'sale_chart': income_dict.get(sale_list_l, 0) - cost_dict.get(sale_list_l, 0),
                        'gross_profit_margin': str(
                            "%.4f" % ((income_dict.get(sale_list_l, 0) - cost_dict.get(sale_list_l,
                                                                                       0)) * 100 / income_dict.get(
                                sale_list_l, 0))) + "%"
                    }
                cre_obj = self.env['qdodoo.sale.chart.report.p'].create(data)
                result_list.append(cre_obj.id)
            return {
                'name': (u'销售毛利汇总表（客户）'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.sale.chart.report.p',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', result_list)],
                'views': [(view_id2, 'tree')],
                'view_id': [view_id2],
            }
