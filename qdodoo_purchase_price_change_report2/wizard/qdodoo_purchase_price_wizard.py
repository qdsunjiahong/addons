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

    search_choice = fields.Selection(((1, u'年份'), (5, u'月份'), (2, u'季度'), (3, u'日期'), (4, u'时间段')),
                                     string=u'查询方式', required=True, default=4)
    year = fields.Many2one('account.fiscalyear', string=u'年度')
    month = fields.Selection((('01', u'一月'), ('02', u'二月'), ('03', u'三月'), ('04', u'四月'),
                              ('05', u'五月'), ('06', u'六月'), ('07', u'七月'), ('08', u'八月'), ('09', u'九月'),
                              ('10', u'十月'), ('11', u'十一月'), ('12', u'十二月')), string=u'月份')
    quarter = fields.Selection((('1', u'第一季度'), ('2', u'第二季度'), ('3', u'第三季度'), ('4', u'第四季度')), string=u'季度')
    company_id = fields.Many2one('res.company', string=u'公司')
    partner_id = fields.Many2one('res.partner', string=u'供应商')
    date = fields.Date(string=u'日期')
    start_date = fields.Date(string=u'开始时间')
    end_date = fields.Date(string=u'结束时间')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_id2 = fields.Many2one('product.product', string=u'产品')

    @api.multi
    def action_done(self):
        report_obj = self.env['qdodoo.purchase.price.report']
        supplier_id = self.env['res.partner'].search([('name', '=', u'前期库存'), ('active', '=', True)])[0].id
        un_ids = report_obj.search([])
        un_ids.unlink()
        model_obj = self.env['ir.model.data']
        result_list = []
        product_list = []
        product_num_dict = {}
        product_amount_dict = {}
        # 年度查询
        if int(self.search_choice) == 1:
            sql_l = """
                select
                    af.name as af_name,
                    pp.name_template as product_name,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    pp.default_code as default_code
                from account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id = ail.product_id
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                    LEFT JOIN account_period ap ON ap.id = ai.period_id
                    LEFT JOIN account_fiscalyear af ON af.id= ap.fiscalyear_id
                where po.state = 'done' and ai.state != 'cancel' and ai.partner_id != %s
            """
            sql_domain = []
            sql_domain.append(supplier_id)
            if self.year:
                year_list = []
                year_ids = self.env['account.fiscalyear'].search([('name', '=', self.year.name)])
                if year_ids and len(year_ids) > 1:
                    for i in year_ids:
                        year_list.append(i.id)
                    sql_l = sql_l + ' and ap.fiscalyear_id in %s'
                    sql_domain.append(tuple(year_list))
                elif year_ids and len(year_ids) == 1:
                    sql_l = sql_l + ' and ap.fiscalyear_id = %s '
                    sql_domain.append(year_ids.id)
            if self.product_id:
                sql_l = sql_l + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            pro_l = []
            if self.product_id2:
                product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                for pr in product_ids:
                    pro_l.append(pr.id)
                if len(pro_l)>1:
                    sql_l = sql_l + ' and ail.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l)==1:
                    sql_l=sql_l+' and ail.product_id = %s'
                    sql_domain.append(pro_l[0])
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
                for i in res:
                    k = (i[0], i[1], i[-1])
                    if k in product_list:
                        product_num_dict[k] += i[2]
                        product_amount_dict[k] += i[3]
                    else:
                        product_num_dict[k] = i[2]
                        product_amount_dict[k] = i[3]
                        product_list.append(k)
                if product_list:
                    for j in product_list:
                        if product_num_dict.get(j, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                        data = {
                            'year': j[0],
                            'product_id': j[1],
                            'default_code': j[-1],
                            'product_qty': product_num_dict.get(j, 0),
                            'price_unit': price_unit,
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
                if result_list:
                    vie_model, view_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                        'qdodoo_purchase_price_report_tree1')
                    view_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                           'qdodoo_purchase_price_report_search1')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                        'search_view_id': [search_id]
                    }
        #####月份查询
        elif int(self.search_choice) == 5:
            sql_l = """
                select
                    ap.name as ap_name,
                    pp.name_template as product_id,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    pp.default_code as default_code
                from account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id = ail.product_id
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                    LEFT JOIN account_period ap ON ap.id = ai.period_id
                where po.state = 'done' and ai.state != 'cancel' and ai.partner_id != %s
            """
            sql_domain = []
            sql_domain.append(supplier_id)
            per_list = []
            year_obj = self.env['account.fiscalyear']
            per_obj = self.env['account.period']
            if self.year and not self.month:
                year_ids = year_obj.search([('name', '=', self.year.name)])
                if year_ids and len(year_ids) > 1:
                    for year_id in year_ids:
                        for per_i in year_id.period_ids:
                            per_list.append(per_i.id)
                    sql_l = sql_l + ' and ai.period_id in %s'
                    sql_domain.append(tuple(per_list))
                elif year_ids and len(year_ids) == 1:
                    sql_l = sql_l + ' and ap.fiscalyear_id = %s '
                    sql_domain.append(year_ids.id)
            elif self.year and self.month:
                per_ids = per_obj.search([('name', '=', str(self.month) + '/' + str(self.year.name))])
                if per_ids and len(per_ids) > 1:
                    for per_id in per_ids:
                        per_list.append(per_id.id)
                    sql_l = sql_l + ' and ai.period_id in %s'
                    sql_domain.append(tuple(per_list))
                elif per_ids and len(per_ids) == 1:
                    sql_l = sql_l + ' and ai.period_id = %s'
                    sql_domain.append(per_ids.id)
            elif not self.year and self.month:
                ye_li = []
                year_ids = year_obj.search([])
                for year_id in year_ids:
                    ye_li.append(str(self.month) + '/' + str(year_id.name))
                per_ids = per_obj.search([('name', 'in', ye_li)])
                if per_ids and len(per_ids) > 1:
                    for per_id in per_ids:
                        per_list.append(per_id.id)
                    sql_l = sql_l + ' and ai.period_id in %s'
                    sql_domain.append(tuple(per_list))
                elif per_ids and len(per_ids) == 1:
                    sql_l = sql_l + ' and ai.period_id = %s'
                    sql_domain.append(per_ids.id)
            if self.product_id:
                sql_l = sql_l + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            pro_l = []
            if self.product_id2:
                product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                for pr in product_ids:
                    pro_l.append(pr.id)
                if len(pro_l)>1:
                    sql_l = sql_l + ' and ail.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l)==1:
                    sql_l=sql_l+' and ail.product_id = %s'
                    sql_domain.append(pro_l[0])
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
                for r in res:
                    k = (r[0], r[1], r[-1])
                    if k in product_list:
                        product_num_dict[k] += r[2]
                        product_amount_dict[k] += r[3]
                    else:
                        product_num_dict[k] = r[2]
                        product_amount_dict[k] = r[3]
                        product_list.append(k)
                for product_l in product_list:
                    if product_num_dict.get(product_l, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0)
                    data = {
                        'period_id': product_l[0],
                        'product_id': product_l[1],
                        'default_code': product_l[-1],
                        'product_qty': product_num_dict.get(product_l, 0),
                        'price_unit': price_unit
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                if result_list:
                    vie_model, view_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                        'qdodoo_purchase_price_report_tree2')
                    view_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                           'qdodoo_purchase_price_report_search2')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                        'search_view_id': [search_id]
                    }
        # # 季度查询
        elif int(self.search_choice) == 2:
            if not self.year:
                year_list = self.env['account.fiscalyear'].search([])
            else:
                year_list = self.env['account.fiscalyear'].search([('name', '=', self.year.name)])
            per_obj = self.env['account.period']
            name_year_list = []  # 年度名称
            quarter_start = {}
            quarter_stop = {}
            quarter_key = []
            if year_list:
                for ye in year_list:
                    if ye.name not in name_year_list and len(str(ye.name)) == 4:
                        name_year_list.append(ye.name)
            for n_year in list(set(name_year_list)):
                if int(self.quarter) == 1:
                    key = str(n_year) + "第一季度"
                    start_p = '01' + '/' + str(n_year)
                    end_p = '03' + '/' + str(n_year)
                    per_starts = per_obj.search([('name', '=', start_p)])
                    if per_starts:
                        quarter_start[key] = per_starts.date_start + " 00:00:01"
                    per_stops = per_obj.search([('name', '=', end_p)])
                    if per_stops:
                        quarter_stop[key] = per_stops[0].date_stop + ' 23:59:59'
                    quarter_key.append(key)
                elif int(self.quarter) == 2:
                    key = str(n_year) + "第二季度"
                    start_p = '04' + '/' + str(n_year)
                    end_p = '06' + '/' + str(n_year)
                    per_starts = per_obj.search([('name', '=', start_p)])
                    if per_starts:
                        quarter_start[key] = per_starts[0].date_start + " 00:00:01"
                    per_stops = per_obj.search([('name', '=', end_p)])
                    if per_stops:
                        quarter_stop[key] = per_stops[0].date_stop + ' 23:59:59'
                    quarter_key.append(key)

                elif int(self.quarter) == 3:
                    key = str(n_year) + "第三季度"
                    start_p = '07' + '/' + str(n_year)
                    end_p = '09' + '/' + str(n_year)
                    per_starts = per_obj.search([('name', '=', start_p)])
                    if per_starts:
                        quarter_start[key] = per_starts[0].date_start + " 00:00:01"
                    per_stops = per_obj.search([('name', '=', end_p)])
                    if per_stops:
                        quarter_stop[key] = per_stops[0].date_stop + ' 23:59:59'
                    quarter_key.append(key)

                elif int(self.quarter) == 4:
                    key = str(n_year) + "第四季度"
                    start_p = '10' + '/' + str(n_year)
                    end_p = '12' + '/' + str(n_year)
                    per_starts = per_obj.search([('name', '=', start_p)])
                    if per_starts:
                        quarter_start[key] = per_starts[0].date_start + " 00:00:01"
                    per_stops = per_obj.search([('name', '=', end_p)])
                    if per_stops:
                        quarter_stop[key] = per_stops[0].date_stop + ' 23:59:59'
                    quarter_key.append(key)
                else:
                    start_p1 = '01' + '/' + str(n_year)
                    end_p1 = '03' + '/' + str(n_year)
                    per_starts1 = per_obj.search([('name', '=', start_p1)])
                    key1 = str(n_year) + "第一季度"
                    if per_starts1:
                        quarter_start[key1] = per_starts1[0].date_start + " 00:00:01"
                    per_stops1 = per_obj.search([('name', '=', end_p1)])
                    if per_stops1:
                        quarter_stop[key1] = per_stops1[0].date_stop + ' 23:59:59'
                    quarter_key.append(key1)
                    start_p2 = '04' + '/' + str(n_year)
                    end_p2 = '06' + '/' + str(n_year)
                    key2 = str(n_year) + "第二季度"
                    per_starts2 = per_obj.search([('name', '=', start_p2)])
                    if per_starts2:
                        quarter_start[key2] = per_starts2[0].date_start + " 00:00:01"
                    per_stops2 = per_obj.search([('name', '=', end_p2)])
                    if per_stops2:
                        quarter_stop[key2] = per_stops2[0].date_stop + ' 23:59:59'
                    quarter_key.append(key2)
                    start_p3 = '07' + '/' + str(n_year)
                    end_p3 = '09' + '/' + str(n_year)
                    key3 = str(n_year) + "第三季度"
                    per_starts3 = per_obj.search([('name', '=', start_p3)])
                    if per_starts3:
                        quarter_start[key3] = per_starts3[0].date_start + " 00:00:01"
                    per_stops3 = per_obj.search([('name', '=', end_p3)])
                    if per_stops3:
                        quarter_stop[key3] = per_stops3[0].date_stop + ' 23:59:59'
                    quarter_key.append(key3)
                    start_p4 = '10' + '/' + str(n_year)
                    end_p4 = '12' + '/' + str(n_year)
                    key4 = str(n_year) + "第四季度"
                    per_starts4 = per_obj.search([('name', '=', start_p4)])
                    if per_starts4:
                        quarter_start[key4] = per_starts4[0].date_start + ' 23:59:59'
                    per_stops4 = per_obj.search([('name', '=', end_p4)])
                    if per_stops4:
                        quarter_stop[key4] = per_stops4[0].date_stop + ' 23:59:59'
                    quarter_key.append(key4)
            for d in quarter_key:
                sql_l = """
                select
                    pp.name_template as product_name,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    pp.default_code as default_code
                from account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id = ail.product_id
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                where po.state = 'done' and ai.state != 'cancel' and ai.partner_id != %s
                """
                sql_domain = []
                sql_domain.append(supplier_id)
                if self.product_id:
                    sql_l = sql_l + ' and ail.product_id = %s'
                    sql_domain.append(self.product_id.id)
                pro_l = []
                if self.product_id2:
                    product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                    for pr in product_ids:
                        pro_l.append(pr.id)
                    if len(pro_l)>1:
                        sql_l = sql_l + ' and ail.product_id in %s'
                        sql_domain.append(tuple(pro_l))
                    elif len(pro_l)==1:
                        sql_l=sql_l+' and ail.product_id = %s'
                        sql_domain.append(pro_l[0])
                if self.partner_id:
                    sql_l = sql_l + ' and ai.partner_id = %s'
                    sql_domain.append(self.partner_id.id)
                if quarter_start.get(d, None) != None:
                    sql_l = sql_l + " and ai.date_invoice >= '%s'"
                    sql_domain.append(quarter_start.get(d))
                if quarter_stop.get(d, None) != None:
                    sql_domain.append(quarter_stop.get(d))
                    sql_l = sql_l + " and ai.date_invoice <= '%s'"
                if self.company_id:
                    sql_l = sql_l + " and ai.company_id = %s"
                    sql_domain.append(self.company_id.id)
                sql = sql_l % tuple(sql_domain)
                self.env.cr.execute(sql)
                res = self.env.cr.fetchall()
                if res:
                    for r in res:
                        k = (d, r[0], r[-1])
                        if k in product_list:
                            product_num_dict[k] += r[1]
                            product_amount_dict[k] += r[2]
                        else:
                            product_num_dict[k] = r[1]
                            product_amount_dict[k] = r[2]
                            product_list.append(k)
            if product_list:
                for product_l in product_list:
                    if product_num_dict.get(product_l, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0)
                    data = {
                        'quarter': product_l[0],
                        'product_id': product_l[1],
                        'default_code': product_l[-1],
                        'price_unit': price_unit,
                        'product_qty': product_num_dict.get(product_l, 0)
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                if result_list:
                    vie_model, view_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                        'qdodoo_purchase_price_report_tree3')
                    view_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                           'qdodoo_purchase_price_report_search3')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                        'search_view_id': [search_id]
                    }

        #####日期查询
        elif int(self.search_choice) == 3:
            sql_l = """
                select
                    pp.name_template as product_name,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    pp.default_code as default_code
                from account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id = ail.product_id
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                where po.state = 'done' and ai.state != 'cancel' and ai.partner_id != %s
            """
            sql_domain = []
            sql_domain.append(supplier_id)
            if self.date:
                sql_l = sql_l + " and ai.date_invoice = '%s'"
                sql_domain.append(self.date)
            if self.product_id:
                sql_l = sql_l + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            pro_l = []
            if self.product_id2:
                product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                for pr in product_ids:
                    pro_l.append(pr.id)
                if len(pro_l)>1:
                    sql_l = sql_l + ' and ail.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l)==1:
                    sql_l=sql_l+' and ail.product_id = %s'
                    sql_domain.append(pro_l[0])
            if self.partner_id:
                sql_l = sql_l + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id and self.company_id.name != u'惠美集团':
                sql_l = sql_l + ' and ai.company_id = %s'
                sql_domain.append(self.company_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                for i in res:
                    k = (i[0], i[-1])
                    if k in product_list:
                        product_num_dict[k] += i[1]
                        product_amount_dict[k] += i[2]
                    else:
                        product_num_dict[k] = i[1]
                        product_amount_dict[k] = i[2]
                        product_list.append(k)
                for product_l in product_list:
                    if product_num_dict.get(product_l, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0)
                    data = {
                        'date': self.date,
                        'product_id': product_l[0],
                        'default_code': product_l[1],
                        'product_qty': product_num_dict.get(product_l, 0),
                        'price_unit': price_unit,
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                if result_list:
                    vie_model, view_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                        'qdodoo_purchase_price_report_tree4')
                    view_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                           'qdodoo_purchase_price_report_search4')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                        'search_view_id': [search_id]
                    }
        #####时间段查询
        elif int(self.search_choice) == 4:
            sql_l = """
                select
                    pp.name_template as product_name,
                    ail.quantity as product_qty,
                    (ail.price_unit * ail.quantity) as product_amount,
                    pp.default_code as default_code
                from account_invoice_line ail
                    LEFT JOIN product_product pp ON pp.id = ail.product_id
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                where po.state = 'done' and ai.state != 'cancel' and ai.partner_id != %s
            """
            sql_domain = []
            sql_domain.append(supplier_id)
            sql_l = sql_l + " and ai.date_invoice >= '%s'"
            sql_domain.append(self.start_date)
            sql_l = sql_l + " and ai.date_invoice <= '%s'"
            sql_domain.append(self.end_date)
            if self.company_id and self.company_id.name != u'惠美集团':
                sql_l = sql_l + ' and ai.company_id = %s'
                sql_domain.append(self.company_id.id)
            if self.product_id:
                sql_l = sql_l + 'and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            pro_l = []
            if self.product_id2:
                product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                for pr in product_ids:
                    pro_l.append(pr.id)
                if len(pro_l)>1:
                    sql_l = sql_l + ' and ail.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l)==1:
                    sql_l=sql_l+' and ail.product_id = %s'
                    sql_domain.append(pro_l[0])
            if self.partner_id:
                sql_l = sql_l + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                for i in res:
                    k = (i[0], i[-1])
                    if k in product_list:
                        product_num_dict[k] += i[1]
                        product_amount_dict[k] += i[2]
                    else:
                        product_num_dict[k] = i[1]
                        product_amount_dict[k] = i[2]
                        product_list.append(k)
                for product_l in product_list:
                    if product_num_dict.get(product_l, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0)
                    data = {
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'product_id': product_l[0],
                        'default_code': product_l[-1],
                        'product_qty': product_num_dict.get(product_l, 0),
                        'price_unit': price_unit,
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                if result_list:
                    vie_model, view_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                        'qdodoo_purchase_price_report_tree5')
                    view_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                           'qdodoo_purchase_price_report_search5')
                    return {
                        'name': _('采购价格变动表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.purchase.price.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                        'search_view_id': [search_id]
                    }
