# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
import copy


class qdodoo_stock_in_analytic_wizard(models.Model):
    _name = 'qdodoo.stock.in.analytic.wizard'
    _description = 'qdodoo.stock.in.analytic.wizard'

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
        report_obj = self.env['qdodoo.stock.in.analytic.report']
        supplier_ids = self.pool.get('res.partner').search(self.env.cr, self.env.uid,
                                                           ['|', '|', ('name', 'ilike', u'期初'),
                                                            ('name', 'ilike', u'前期'), '&',
                                                            ('is_internal_company', '=', True),
                                                            ('supplier', '=', True)])
        un_ids = report_obj.search([])
        un_ids.unlink()
        sql_select = """
            ai.partner_id as partner_id,
            pp.name_template as product_name,
            pp.default_code as default_code,
            ail.quantity as product_qty,
            ail.price_unit as price_unit,
            (ail.price_unit * ail.quantity) as product_amount,
            pt.uom_po_id as uom_id,
            po.location_id as location_id,
            po.payment_term_id as payment_term_id,
            ail.company_id as company_id,
            ai.date_invoice as date
        """
        sql_from = """
            from account_invoice_line ail
            LEFT JOIN product_product pp ON pp.id = ail.product_id
            LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
        """
        sql_where = """
        where po.state = 'done' and ai.state != 'cancel'
        """
        sql_domain = []
        model_obj = self.env['ir.model.data']
        if len(supplier_ids) == 1:
            sql_where = sql_where + " and ail.partner_id != %s"
            sql_domain.append(supplier_ids[0])
        elif len(supplier_ids) > 1:
            sql_where = sql_where + " and ail.partner_id not in %s"
            sql_domain.append(tuple(supplier_ids))
        result_list = []
        product_list = []
        product_num_dict = {}
        product_amount_dict = {}
        # 年度查询
        if int(self.search_choice) == 1:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                 'qdodoo_stock_in_analytic_report1')
            search_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                     'qdodoo_stock_in_analytic_search1')
            sql_select = 'af.name as name,' + sql_select
            sql_from = sql_from + """
                LEFT JOIN account_period ap ON ap.id = ai.period_id
                LEFT JOIN account_fiscalyear af ON af.id= ap.fiscalyear_id
            """
            if self.year:
                year_list = []
                year_ids = self.env['account.fiscalyear'].search([('name', '=', self.year.name)])
                if year_ids and len(year_ids) > 1:
                    for i in year_ids:
                        year_list.append(i.id)
                    sql_where = sql_where + ' and ap.fiscalyear_id in %s'
                    sql_domain.append(tuple(year_list))
                elif year_ids and len(year_ids) == 1:
                    sql_where = sql_where + ' and ap.fiscalyear_id = %s '
                    sql_domain.append(year_ids.id)
            if self.product_id:
                sql_where = sql_where + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            pro_l = []
            if self.product_id2:
                product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                for pr in product_ids:
                    pro_l.append(pr.id)
                if len(pro_l) > 1:
                    sql_where = sql_where + ' and ail.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l) == 1:
                    sql_where = sql_where + ' and ail.product_id = %s'
                    sql_domain.append(pro_l[0])
            if self.partner_id:
                sql_where = sql_where + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id and self.company_id.name != u'惠美集团':
                sql_where = sql_where + ' and ai.company_id=%s'
                sql_domain.append(self.company_id.id)
            sql_l = "select " + sql_select + sql_from + sql_where
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                for i in res:
                    data1 = {
                        'year': i[0],
                        'partner_id': i[1],
                        'product_id': i[2],
                        'default_code': i[3],
                        'product_qty': i[4],
                        'price_unit': i[5],
                        'product_amount': i[6],
                        'location_id': i[8],
                        'company_id': i[10],
                        'uom_id': i[7],
                        'date': i[-1]
                    }
                    if i[9]:
                        data1['property_supplier_payment_term'] = i[9]
                    cre_obj1 = report_obj.create(data1)
                    result_list.append(cre_obj1.id)
                    # (年份，供应商，产品，编码，单位，公司)
                    k = (i[0], i[1], i[2], i[3], i[7], i[10])
                    if k in product_list:
                        product_num_dict[k] += i[4]
                        product_amount_dict[k] += i[6]
                    else:
                        product_num_dict[k] = i[4]
                        product_amount_dict[k] = i[6]
                        product_list.append(k)
                if product_list:
                    for j in product_list:
                        if product_num_dict.get(j, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                        data = {
                            'year': j[0],
                            'partner_id': j[1],
                            'product_id': j[2],
                            'default_code': j[3],
                            'product_qty': product_num_dict.get(j, 0),
                            'price_unit': price_unit,
                            'product_amount': product_amount_dict.get(j, 0),
                            'uom_id': j[4],
                            'company_id': j[5]
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
        #####月份查询
        elif int(self.search_choice) == 5:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                 'qdodoo_stock_in_analytic_report5')
            search_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                     'qdodoo_stock_in_analytic_search5')
            sql_select = 'ap.name as ap_name,' + sql_select
            sql_from = sql_from + "LEFT JOIN account_period ap ON ap.id = ai.period_id"
            per_list = []
            year_obj = self.env['account.fiscalyear']
            per_obj = self.env['account.period']
            if self.year and not self.month:
                year_ids = year_obj.search([('name', '=', self.year.name)])
                if year_ids and len(year_ids) > 1:
                    for year_id in year_ids:
                        for per_i in year_id.period_ids:
                            per_list.append(per_i.id)
                    sql_where = sql_where + ' and ai.period_id in %s'
                    sql_domain.append(tuple(per_list))
                elif year_ids and len(year_ids) == 1:
                    sql_where = sql_where + ' and ap.fiscalyear_id = %s '
                    sql_domain.append(year_ids.id)
            elif self.year and self.month:
                per_ids = per_obj.search([('name', '=', str(self.month) + '/' + str(self.year.name))])
                if per_ids and len(per_ids) > 1:
                    for per_id in per_ids:
                        per_list.append(per_id.id)
                    sql_where = sql_where + ' and ai.period_id in %s'
                    sql_domain.append(tuple(per_list))
                elif per_ids and len(per_ids) == 1:
                    sql_where = sql_where + ' and ai.period_id = %s'
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
                    sql_where = sql_where + ' and ai.period_id in %s'
                    sql_domain.append(tuple(per_list))
                elif per_ids and len(per_ids) == 1:
                    sql_where = sql_where + ' and ai.period_id = %s'
                    sql_domain.append(per_ids.id)
            if self.product_id:
                sql_where = sql_where + ' and ail.product_id = %s'
                sql_domain.append(self.product_id.id)
            pro_l = []
            if self.product_id2:
                product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                for pr in product_ids:
                    pro_l.append(pr.id)
                if len(pro_l) > 1:
                    sql_where = sql_where + ' and ail.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l) == 1:
                    sql_where = sql_where + ' and ail.product_id = %s'
                    sql_domain.append(pro_l[0])
            if self.partner_id:
                sql_where = sql_where + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id and self.company_id.name != u'惠美集团':
                sql_where = sql_where + ' and ai.company_id = %s'
                sql_domain.append(self.company_id.id)
            sql_l = "select " + sql_select + sql_from + sql_where
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                for i in res:
                    data1 = {
                        'period_id': i[0],
                        'partner_id': i[1],
                        'product_id': i[2],
                        'default_code': i[3],
                        'product_qty': i[4],
                        'price_unit': i[5],
                        'product_amount': i[6],
                        'location_id': i[8],
                        'company_id': i[10],
                        'uom_id': i[7],
                        'date': i[-1]
                    }
                    if i[9]:
                        data1['property_supplier_payment_term'] = i[9]
                    cre_obj1 = report_obj.create(data1)
                    result_list.append(cre_obj1.id)
                    # (月份，供应商，产品，编码，单位，公司)
                    k = (i[0], i[1], i[2], i[3], i[7], i[10])
                    if k in product_list:
                        product_num_dict[k] += i[4]
                        product_amount_dict[k] += i[6]
                    else:
                        product_num_dict[k] = i[4]
                        product_amount_dict[k] = i[6]
                        product_list.append(k)
                if product_list:
                    for j in product_list:
                        if product_num_dict.get(j, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                        data = {
                            'period_id': j[0],
                            'partner_id': j[1],
                            'product_id': j[2],
                            'default_code': j[3],
                            'product_qty': product_num_dict.get(j, 0),
                            'price_unit': price_unit,
                            'product_amount': product_amount_dict.get(j, 0),
                            'uom_id': j[4],
                            'company_id': j[5]
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
        # # 季度查询
        elif int(self.search_choice) == 2:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                 'qdodoo_stock_in_analytic_report2')
            search_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                     'qdodoo_stock_in_analytic_search2')
            sql_l = "select " + sql_select + sql_from + sql_where
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
                        quarter_start[key] = per_starts[0].date_start + " 00:00:01"
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
                sql_domain2 = copy.deepcopy(sql_domain)
                sql_l2 = sql_l
                if self.product_id:
                    sql_l2 = sql_l2 + ' and ail.product_id = %s'
                    sql_domain2.append(self.product_id.id)
                pro_l = []
                if self.product_id2:
                    product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                    for pr in product_ids:
                        pro_l.append(pr.id)
                    if len(pro_l) > 1:
                        sql_l2 = sql_l2 + ' and ail.product_id in %s'
                        sql_domain2.append(tuple(pro_l))
                    elif len(pro_l) == 1:
                        sql_l2 = sql_l2 + ' and ail.product_id = %s'
                        sql_domain2.append(pro_l[0])
                if self.partner_id:
                    sql_l2 = sql_l2 + ' and ai.partner_id = %s'
                    sql_domain2.append(self.partner_id.id)
                if quarter_start.get(d, None) != None:
                    sql_l2 = sql_l2 + " and ai.date_invoice >= '%s'"
                    sql_domain2.append(quarter_start.get(d))
                if quarter_stop.get(d, None) != None:
                    sql_domain2.append(quarter_stop.get(d))
                    sql_l2 = sql_l2 + " and ai.date_invoice <= '%s'"
                if self.company_id:
                    sql_l2 = sql_l2 + " and ai.company_id = %s"
                    sql_domain2.append(self.company_id.id)
                sql = sql_l2 % tuple(sql_domain2)
                self.env.cr.execute(sql)
                res = self.env.cr.fetchall()
                if res:
                    for i in res:
                        data1 = {
                            'quarter': d,
                            'partner_id': i[0],
                            'product_id': i[1],
                            'default_code': i[2],
                            'product_qty': i[3],
                            'price_unit': i[4],
                            'product_amount': i[5],
                            'location_id': i[7],
                            'company_id': i[9],
                            'uom_id': i[6],
                            'date': i[-1]
                        }
                        if i[8]:
                            data1['property_supplier_payment_term'] = i[8]
                        cre_obj1 = report_obj.create(data1)
                        result_list.append(cre_obj1.id)
                        # (季度，供应商，产品，编码，单位，公司)
                        k = (d, i[0], i[1], i[2], i[6], i[9])
                        if k in product_list:
                            product_num_dict[k] += i[3]
                            product_amount_dict[k] += i[5]
                        else:
                            product_num_dict[k] = i[3]
                            product_amount_dict[k] = i[5]
                            product_list.append(k)
            if product_list:
                for product_l in product_list:
                    if product_num_dict.get(product_l, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0)
                    data = {
                        'quarter': product_l[0],
                        'partner_id': product_l[1],
                        'product_id': product_l[2],
                        'default_code': product_l[3],
                        'company_id': product_l[5],
                        'price_unit': price_unit,
                        'product_qty': product_num_dict.get(product_l, 0),
                        'product_amount': product_amount_dict.get(product_l, 0),
                        'uom_id': product_l[4]
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
        #####日期查询
        elif int(self.search_choice) == 3:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                 'qdodoo_stock_in_analytic_report3')
            search_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                     'qdodoo_stock_in_analytic_search3')
            sql_l = "select " + sql_select + sql_from + sql_where

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
                if len(pro_l) > 1:
                    sql_l = sql_l + ' and ail.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l) == 1:
                    sql_l = sql_l + ' and ail.product_id = %s'
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
                    data1 = {
                        'date': self.date,
                        'partner_id': i[0],
                        'product_id': i[1],
                        'default_code': i[2],
                        'product_qty': i[3],
                        'price_unit': i[4],
                        'product_amount': i[5],
                        'location_id': i[7],
                        'company_id': i[9],
                        'uom_id': i[6]
                    }
                    if i[8]:
                        data1['property_supplier_payment_term'] = i[8]
                    cre_obj1 = report_obj.create(data1)
                    result_list.append(cre_obj1.id)
                    # (日期，供应商，产品，编码，单位，公司)
                    k = (self.date, i[0], i[1], i[2], i[6], i[9])
                    if k in product_list:
                        product_num_dict[k] += i[3]
                        product_amount_dict[k] += i[5]
                    else:
                        product_num_dict[k] = i[3]
                        product_amount_dict[k] = i[5]
                        product_list.append(k)
                if product_list:
                    for product_l in product_list:
                        if product_num_dict.get(product_l, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0)
                        data = {
                            'date': product_l[0],
                            'partner_id': product_l[1],
                            'product_id': product_l[2],
                            'default_code': product_l[3],
                            'company_id': product_l[5],
                            'price_unit': price_unit,
                            'product_qty': product_num_dict.get(product_l, 0),
                            'product_amount': product_amount_dict.get(product_l, 0),
                            'uom_id': product_l[4]
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
        #####时间段查询
        else:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                 'qdodoo_stock_in_analytic_report4')
            search_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                     'qdodoo_stock_in_analytic_search4')
            sql_l = "select " + sql_select + sql_from + sql_where
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
                if len(pro_l) > 1:
                    sql_l = sql_l + ' and ail.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l) == 1:
                    sql_l = sql_l + ' and ail.product_id = %s'
                    sql_domain.append(pro_l[0])
            if self.partner_id:
                sql_l = sql_l + ' and ai.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                for i in res:
                    data1 = {
                        'partner_id': i[0],
                        'product_id': i[1],
                        'default_code': i[2],
                        'product_qty': i[3],
                        'price_unit': i[4],
                        'product_amount': i[5],
                        'location_id': i[7],
                        'company_id': i[9],
                        'uom_id': i[6],
                        'date': i[-1]
                    }
                    if i[8]:
                        data1['property_supplier_payment_term'] = i[8]
                    cre_obj1 = report_obj.create(data1)
                    result_list.append(cre_obj1.id)
                    # (供应商，产品，编码，单位，公司)
                    k = (i[0], i[1], i[2], i[6], i[9])
                    if k in product_list:
                        product_num_dict[k] += i[3]
                        product_amount_dict[k] += i[5]
                    else:
                        product_num_dict[k] = i[3]
                        product_amount_dict[k] = i[5]
                        product_list.append(k)
                if product_list:
                    for product_l in product_list:
                        if product_num_dict.get(product_l, 0) == 0:
                            price_unit = 0
                        else:
                            price_unit = product_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0)
                        data = {
                            'partner_id': product_l[0],
                            'product_id': product_l[1],
                            'default_code': product_l[2],
                            'company_id': product_l[4],
                            'price_unit': price_unit,
                            'product_qty': product_num_dict.get(product_l, 0),
                            'product_amount': product_amount_dict.get(product_l, 0),
                            'uom_id': product_l[3]
                        }
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
        if result_list:
            return {
                'name': _('入库分析表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.stock.in.analytic.report',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', result_list)],
                'views': [(tree_id, 'tree')],
                'view_id': [tree_id],
                'search_view_id': [search_id]
            }
        else:
            raise except_orm(_(u'警告'), _(u'未查询到数据'))
