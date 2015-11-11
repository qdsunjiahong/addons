# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_purchase_price_wizard(models.Model):
    _name = 'qdodoo.purchase.price.wizard'
    _description = 'qdodoo.purchase.price.wizard'

    search_choice = fields.Selection(((1, u'年度'), (2, u'季度'), (6, u'月份'), (3, u'供应商'), (4, u'日期'), (5, u'时间段')),
                                     string=u'查询方式', required=True, default=5)
    company_id = fields.Many2one('res.company', string=u'公司')
    partner_id = fields.Many2one('res.partner', string=u'供应商')
    date = fields.Date(string=u'日期')
    start_date = fields.Date(string=u'开始时间')
    end_date = fields.Date(string=u'结束时间')
    product_id = fields.Many2one('product.product', string=u'产品')

    @api.multi
    def action_done(self):
        report_obj = self.env['qdodoo.purchase.price.report']
        mod_obj = self.env['ir.model.data']
        result_list = []
        if int(self.search_choice) == 1:
            sql_l = """
                select
                    af.id as af_id,
                    ai.period_id as period_id,
                    ail.product_id as product_id,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    po.location_id as location_id,
                    po.partner_id as partner_id,
                    po.company_id as company_id
                from account_invoice_line ail
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                    LEFT JOIN account_journal aj ON aj.id = ai.journal_id
                    LEFT JOIN account_period ap ON ap.id = ai.period_id
                    LEFT JOIN account_fiscalyear af ON af.id=ap.fiscalyear_id
                where po.state = 'done' and ai.state != 'cancel'
            """
            sql_domain = []
            if self.product_id:
                sql_l = sql_l + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            if self.partner_id:
                sql_l = sql_l + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id and self.company_id.name != u'惠美集团':
                sql_l = sql_l + ' and ai.company_id=%s'
                sql_domain.append(self.company_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                fiscalyear_list = []
                product_num_dict = {}
                product_amount_dict = {}
                for i in res:
                    k = (i[0], i[2], i[5], i[6], i[7])
                    if k in fiscalyear_list:
                        product_num_dict[k] += i[3]
                        product_amount_dict[k] += i[4]
                    else:
                        product_num_dict[k] = i[3]
                        product_amount_dict[k] = i[3]
                        fiscalyear_list.append(k)
                if fiscalyear_list:
                    for j in fiscalyear_list:
                        if product_num_dict.get(j, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                        data = {
                            'year': j[0],
                            'partner_id': j[3],
                            'product_id': j[1],
                            'product_qty': product_num_dict.get(j, 0),
                            'price_unit': price_unit,
                            'location_id': j[2],
                            'company_id': j[4]
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
                    view_mode, view_id = mod_obj.get_object_reference('qdodoo_purchase_price_change_report',
                                                                      'qdodoo_purchase_price_report_tree1')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                    }
        elif int(self.search_choice) == 2:
            if self.company_id and self.company_id.name != u'惠美集团':
                year_list = self.env['account.fiscalyear'].search([('company_id', '=', self.company_id.id)])
            else:
                year_list = self.env['account.fiscalyear'].search([])
            per_obj = self.env['account.period']
            y_dict = {}
            product_list = []
            res_list = []
            product_num_dict = {}
            product_amount_dict = {}
            result_list = []
            if year_list:
                for y in year_list:
                    p1_list = []
                    p2_list = []
                    p3_list = []
                    p4_list = []
                    do1 = [('fiscalyear_id', '=', y.id), (
                        'name', 'in', ('01/' + str(y.name), '02/' + str(y.name), '03/' + str(y.name)))]
                    do2 = [('fiscalyear_id', '=', y.id),
                           ('name', 'in', ('04/' + str(y.name), '05/' + str(y.name), '06/' + str(y.name)))]
                    do3 = [('fiscalyear_id', '=', y.id),
                           ('name', 'in', ('07/' + str(y.name), '08/' + str(y.name), '09/' + str(y.name)))]
                    do4 = [('fiscalyear_id', '=', y.id),
                           ('name', 'in', ('10/' + str(y.name), '11/' + str(y.name), '12/' + str(y.name)))]
                    per_ids1 = per_obj.search(do1)
                    if per_ids1:
                        for p1 in per_ids1:
                            p1_list.append(p1.id)
                    per_ids2 = per_obj.search(do2)
                    if per_ids2:
                        for p2 in per_ids2:
                            p2_list.append(p2.id)
                    per_ids3 = per_obj.search(do3)
                    if per_ids3:
                        for p3 in per_ids3:
                            p3_list.append(p3.id)
                    per_ids4 = per_obj.search(do4)
                    if per_ids4:
                        for p4 in per_ids4:
                            p4_list.append(p4.id)
                    k1 = (str(y.name) + "第一季度", y.id)
                    k2 = (str(y.name) + "第二季度", y.id)
                    k3 = (str(y.name) + "第三季度", y.id)
                    k4 = (str(y.name) + "第四季度", y.id)
                    y_dict[k1] = p1_list
                    y_dict[k2] = p2_list
                    y_dict[k3] = p3_list
                    y_dict[k4] = p4_list
                for i in y_dict.keys():
                    if y_dict.get(i, []):
                        sql_l = """
                            select
                                af.id as af_id,
                                ai.period_id as period_id,
                                ail.product_id as product_id,
                                ail.quantity as product_qty,
                                (ail.price_unit * ail.quantity) as product_amount,
                                po.location_id as location_id,
                                po.partner_id as partner_id,
                                po.company_id as company_id
                            from account_invoice_line ail
                                LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                                LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                                LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                                LEFT JOIN account_journal aj ON aj.id = ai.journal_id
                                LEFT JOIN account_period ap ON ap.id = ai.period_id
                                LEFT JOIN account_fiscalyear af ON af.id=ap.fiscalyear_id
                            where po.state = 'done' and ai.state != 'cancel'
                        """
                        sql_domain = []
                        if self.product_id:
                            sql_l = sql_l + ' and ail.product_id = %s'
                            sql_domain.append(self.product_id.id)
                        if self.partner_id:
                            sql_l = sql_l + ' and ai.partner_id = %s'
                            sql_domain.append(self.partner_id.id)
                        if self.company_id and self.company_id.name != u'惠美集团':
                            sql_l = sql_l + ' and ai.company_id=%s'
                            sql_domain.append(self.company_id.id)
                        p_list = y_dict.get(i)
                        sql_l = sql_l + ' and ai.period_id in %s'
                        sql_domain.append(tuple(p_list))
                        sql = sql_l % tuple(sql_domain)
                        self.env.cr.execute(sql)
                        res = self.env.cr.fetchall()
                        if res:
                            for j in res:
                                k = (i, j[2], j[5], j[6], j[7])
                                if k in product_list:
                                    product_num_dict[k] += j[3]
                                    product_amount_dict[k] += j[4]
                                else:
                                    product_num_dict[k] = j[3]
                                    product_amount_dict[k] = j[4]
                                    product_list.append(k)
                for ll in product_list:
                    if product_num_dict.get(ll, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(ll, 0) / product_num_dict.get(ll, 0)
                    data = {
                        'quarter': ll[0][0],
                        'partner_id': ll[3],
                        'product_id': ll[1],
                        'location_id': ll[2],
                        'company_id': ll[4],
                        'product_qty': product_num_dict.get(ll, 0),
                        'price_unit': price_unit
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                if result_list:
                    view_mode, view_id = mod_obj.get_object_reference('qdodoo_purchase_price_change_report',
                                                                      'qdodoo_purchase_price_report_tree5')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                    }




        elif int(self.search_choice) == 6:
            sql_l = """
                select
                    af.id as af_id,
                    ai.period_id as period_id,
                    ail.product_id as product_id,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    po.location_id as location_id,
                    po.partner_id as partner_id,
                    po.company_id as company_id
                from account_invoice_line ail
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                    LEFT JOIN account_journal aj ON aj.id = ai.journal_id
                    LEFT JOIN account_period ap ON ap.id = ai.period_id
                    LEFT JOIN account_fiscalyear af ON af.id=ap.fiscalyear_id
                where po.state = 'done' and ai.state != 'cancel'
            """
            sql_domain = []
            if self.product_id:
                sql_l = sql_l + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            if self.partner_id:
                sql_l = sql_l + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id and self.company_id.name != u'惠美集团':
                sql_l = sql_l + ' and ai.company_id=%s'
                sql_domain.append(self.company_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                month_list = []
                product_num_dict = {}
                product_amount_dict = {}
                for i in res:
                    k = (i[1], i[2], i[5], i[6], i[7])
                    if k in month_list:
                        product_num_dict[k] += i[3]
                        product_amount_dict[k] += i[4]
                    else:
                        product_num_dict[k] = i[3]
                        product_amount_dict[k] = i[4]
                        month_list.append(k)
                if month_list:
                    for j in month_list:
                        if product_num_dict.get(j, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                        data = {
                            'period_id': j[0],
                            'partner_id': j[3],
                            'product_id': j[1],
                            'product_qty': product_num_dict.get(j, 0),
                            'price_unit': price_unit,
                            'location_id': j[2],
                            'company_id': j[4]
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
                    view_mode, view_id = mod_obj.get_object_reference('qdodoo_purchase_price_change_report',
                                                                      'qdodoo_purchase_price_report_tree2')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                    }

        elif int(self.search_choice) == 3:
            sql_l = """
                select
                    af.id as af_id,
                    ai.period_id as period_id,
                    ail.product_id as product_id,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    po.location_id as location_id,
                    po.partner_id as partner_id,
                    po.company_id as company_id
                from account_invoice_line ail
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                    LEFT JOIN account_journal aj ON aj.id = ai.journal_id
                    LEFT JOIN account_period ap ON ap.id = ai.period_id
                    LEFT JOIN account_fiscalyear af ON af.id=ap.fiscalyear_id
                where po.state = 'done' and ai.state != 'cancel'
            """

            sql_domain = []
            if self.product_id:
                sql_l = sql_l + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            if self.partner_id:
                sql_l = sql_l + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id and self.company_id.name != u'惠美集团':
                sql_l = sql_l + ' and ai.company_id=%s'
                sql_domain.append(self.company_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                partner_list = []
                product_num_dict = {}
                product_amount_dict = {}
                for i in res:
                    k = (i[2], i[5], i[6], i[7])
                    if k in partner_list:
                        product_num_dict[k] += i[3]
                        product_amount_dict[k] += i[4]
                    else:
                        product_num_dict[k] = i[3]
                        product_amount_dict[k] = i[4]
                        partner_list.append(k)
                if partner_list:
                    for j in partner_list:
                        if product_num_dict.get(j, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                        data = {
                            'partner_id': j[2],
                            'product_id': j[0],
                            'product_qty': product_num_dict.get(j, 0),
                            'price_unit': price_unit,
                            'location_id': j[1],
                            'company_id': j[3]
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
                    view_mode, view_id = mod_obj.get_object_reference('qdodoo_purchase_price_change_report',
                                                                      'qdodoo_purchase_price_report_tree3')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                    }
        elif int(self.search_choice) == 4 and self.date:
            sql_l = """
                select
                    af.id as af_id,
                    ai.period_id as period_id,
                    ail.product_id as product_id,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    po.location_id as location_id,
                    po.partner_id as partner_id,
                    po.company_id as company_id
                from account_invoice_line ail
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                    LEFT JOIN account_journal aj ON aj.id = ai.journal_id
                    LEFT JOIN account_period ap ON ap.id = ai.period_id
                    LEFT JOIN account_fiscalyear af ON af.id=ap.fiscalyear_id
                where po.state = 'done' and ai.state != 'cancel' and ai.date_invoice='%s'
            """
            sql_domain = []
            sql_domain.append(self.date)
            if self.product_id:
                sql_l = sql_l + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            if self.partner_id:
                sql_l = sql_l + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id and self.company_id.name != u'惠美集团':
                sql_l = sql_l + ' and ai.company_id=%s'
                sql_domain.append(self.company_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                product_list = []
                product_num_dict = {}
                product_amount_dict = {}
                for i in res:
                    k = (i[2], i[5], i[6], i[7])
                    if k in product_list:
                        product_num_dict[k] += i[3]
                        product_amount_dict[k] += i[4]
                    else:
                        product_num_dict[k] = i[3]
                        product_amount_dict[k] = i[4]
                        product_list.append(k)
                if product_list:
                    for j in product_list:
                        if product_num_dict.get(j, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                        data = {
                            'date': self.date,
                            'partner_id': j[2],
                            'product_id': j[0],
                            'product_qty': product_num_dict.get(j, 0),
                            'price_unit': price_unit,
                            'location_id': j[1],
                            'company_id': j[3]
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
                    view_mode, view_id = mod_obj.get_object_reference('qdodoo_purchase_price_change_report',
                                                                      'qdodoo_purchase_price_report_tree4')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                    }
        elif int(self.search_choice) == 5 and self.start_date and self.end_date:
            sql_l = """
                select
                    af.id as af_id,
                    ai.period_id as period_id,
                    ail.product_id as product_id,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    po.location_id as location_id,
                    po.partner_id as partner_id,
                    po.company_id as company_id
                from account_invoice_line ail
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                    LEFT JOIN account_journal aj ON aj.id = ai.journal_id
                    LEFT JOIN account_period ap ON ap.id = ai.period_id
                    LEFT JOIN account_fiscalyear af ON af.id=ap.fiscalyear_id
                where po.state = 'done' and ai.state != 'cancel' and ai.date_invoice >= '%s' and ai.date_invoice <= '%s'
            """
            sql_domain = []
            sql_domain.append(self.start_date)
            sql_domain.append(self.end_date)
            if self.product_id:
                sql_l = sql_l + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            if self.partner_id:
                sql_l = sql_l + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id and self.company_id.name != u'惠美集团':
                sql_l = sql_l + ' and ai.company_id=%s'
                sql_domain.append(self.company_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                product_list = []
                product_num_dict = {}
                product_amount_dict = {}
                for i in res:
                    k = (i[2], i[5], i[6], i[7])
                    if k in product_list:
                        product_num_dict[k] += i[3]
                        product_amount_dict[k] += i[4]
                    else:
                        product_num_dict[k] = i[3]
                        product_amount_dict[k] = i[4]
                        product_list.append(k)
                if product_list:
                    for j in product_list:
                        if product_num_dict.get(j, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                        data = {
                            'partner_id': j[2],
                            'product_id': j[0],
                            'product_qty': product_num_dict.get(j, 0),
                            'price_unit': price_unit,
                            'location_id': j[1],
                            'company_id': j[3]
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
                    view_mode, view_id = mod_obj.get_object_reference('qdodoo_purchase_price_change_report',
                                                                      'qdodoo_purchase_price_report_tree3')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                    }
