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
        supplier_ids = self.pool.get('res.partner').search(self.env.cr, self.env.uid,
                                                           ['|', '|', ('name', 'ilike', u'期初'),
                                                            ('name', 'ilike', u'前期'), '&',
                                                            ('is_internal_company', '=', True),
                                                            ('supplier', '=', True)])
        un_ids = report_obj.search([])
        un_ids.unlink()
        sql_select_base = """
        select
            ai.date_invoice as date,
            pp.name_template as product_name,
            pp.default_code as default_code,
            ail.quantity as product_qty,
            (ail.price_unit * ail.quantity) as product_amount,
            pt.uom_po_id as uom_id

        """
        sql_from_base = """
        from account_invoice_line ail
            LEFT JOIN product_product pp ON pp.id = ail.product_id
            LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
        """
        sql_where_base = """
        where ai.state != 'cancel' and pt.type != 'service'
        """
        ####################
        sql1_from_base = """
            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
        """
        sql2_from_base = """
            LEFT JOIN account_invoice ai on ai.id = ail.invoice_id

        """
        sql_domain = []
        model_obj = self.env['ir.model.data']
        if len(supplier_ids) == 1:
            sql_where_base = sql_where_base + " and ail.partner_id != %s"
            sql_domain.append(supplier_ids[0])
        elif len(supplier_ids) > 1:
            sql_where_base = sql_where_base + " and ail.partner_id not in %s"
            sql_domain.append(tuple(supplier_ids))
        if self.product_id:
            sql_where_base = sql_where_base + ' and ail.product_id = %s'
            sql_domain.append(self.product_id.id)
        pro_l = []
        if self.product_id2:
            product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
            for pr in product_ids:
                pro_l.append(pr.id)
            if len(pro_l) > 1:
                sql_where_base = sql_where_base + ' and ail.product_id in %s'
                sql_domain.append(tuple(pro_l))
            elif len(pro_l) == 1:
                sql_where_base = sql_where_base + ' and ail.product_id = %s'
                sql_domain.append(pro_l[0])
        if self.partner_id:
            sql_where_base = sql_where_base + ' and ai.partner_id = %s'
            sql_domain.append(self.partner_id.id)
        if self.company_id:
            sql_where_base = sql_where_base + ' and ai.company_id=%s'
            sql_domain.append(self.company_id.id)
        result_list = []
        product_list = []
        product_num_dict = {}
        product_amount_dict = {}
        # 年度查询
        if int(self.search_choice) == 1:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                 'qdodoo_purchase_price_report_tree1')
            search_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                     'qdodoo_purchase_price_report_search1')
            if self.year:
                sql_where_base = sql_where_base + " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s'"
                sql_domain.append(self.year.date_start)
                sql_domain.append(self.year.date_stop)
            sql_l1 = sql_select_base + sql_from_base + sql1_from_base + sql_where_base
            sql_l2 = sql_select_base + sql_from_base + sql2_from_base + sql_where_base + " and ai.type = 'in_refund'"
            sql = sql_l1 % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                for i in res:
                    if i[0]:
                        year_l = i[0][:4]
                        # (产品，编码，单位,年份)
                        k = (i[1], i[2], i[5], year_l)
                        if k in product_list:
                            product_num_dict[k] += i[3]
                            product_amount_dict[k] += i[4]
                        else:
                            product_num_dict[k] = i[3]
                            product_amount_dict[k] = i[4]
                            product_list.append(k)
            sql2 = sql_l2 % tuple(sql_domain)
            self.env.cr.execute(sql2)
            res2 = self.env.cr.fetchall()
            if res2:
                for i2 in res2:
                    if i[2]:
                        year_l2 = i2[0][:4]
                        # (产品，编码，单位,年份)
                        k2 = (i[1], i[2], i[5], year_l2)
                        if k2 in product_list:
                            product_num_dict[k2] -= i2[3]
                            product_amount_dict[k2] -= i2[4]
                        else:
                            product_num_dict[k2] = -i2[3]
                            product_amount_dict[k2] = -i2[4]
                            product_list.append(k2)
            if product_list:
                for j in product_list:
                    if product_num_dict.get(j, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                    data = {
                        'year': j[3],
                        'product_id': j[0],
                        'default_code': j[1],
                        'product_qty': product_num_dict.get(j, 0),
                        'price_unit': price_unit,
                        'product_amount': product_amount_dict.get(j, 0),
                        'uom_id': j[2]
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
        #####月份查询
        elif int(self.search_choice) == 5:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                 'qdodoo_purchase_price_report_tree2')
            search_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                     'qdodoo_purchase_price_report_search2')
            per_list = []
            year_obj = self.env['account.fiscalyear']
            per_obj = self.env['account.period']
            if self.year and not self.month:
                for per_i in self.year.period_ids:
                    per_list.append((per_i.name, per_i.date_start, per_i.date_stop))
            elif self.year and self.month:
                per_ids = per_obj.search([('name', '=', str(self.month) + '/' + str(self.year.name))])
                if per_ids:
                    per_list.append((per_ids[0].name, per_ids[0].date_start, per_ids[0].date_stop))
            elif not self.year and self.month:
                ye_li = []
                year_ids = year_obj.search([])
                for year_id in list(set(year_ids)):
                    ye_li.append(str(self.month) + '/' + str(year_id.name))
                per_ids = per_obj.search([('name', 'in', ye_li)])
                if per_ids:
                    for per_id in per_ids:
                        per_list.append((per_id.name, per_id.date_start, per_id.date_stop))
            else:
                year_ids = year_obj.search([])
                for year_id in list(set(year_ids)):
                    for per_id in year_id.period_ids:
                        per_list.append((per_id.name, per_id.date_start, per_id.date_stop))
            for per_ids_l in per_list:
                sql_domain_per = copy.deepcopy(sql_domain)
                sql_where_base2 = sql_where_base
                sql_where_base2 = sql_where_base2 + " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s'"
                sql_l1 = sql_select_base + sql_from_base + sql1_from_base + sql_where_base2
                sql_l2 = sql_select_base + sql_from_base + sql2_from_base + sql_where_base2 + " and ai.type = 'in_refund'"
                sql_domain_per.append(per_ids_l[1])
                sql_domain_per.append(per_ids_l[2])
                sql1 = sql_l1 % tuple(sql_domain_per)
                self.env.cr.execute(sql1)
                res = self.env.cr.fetchall()
                month_l = per_ids_l[0]
                if res:
                    for i in res:
                        # (产品，编码，单位，月份)
                        k = (i[1], i[2], i[5], month_l)
                        if k in product_list:
                            product_num_dict[k] += i[3]
                            product_amount_dict[k] += i[4]
                        else:
                            product_num_dict[k] = i[3]
                            product_amount_dict[k] = i[4]
                            product_list.append(k)
                sql2 = sql_l2 % tuple(sql_domain_per)
                self.env.cr.execute(sql2)
                res2 = self.env.cr.fetchall()
                if res2:
                    for i2 in res2:
                        # (产品，编码，单位，月份)
                        k2 = (i2[1], i2[2], i2[5], month_l)
                        if k2 in product_list:
                            product_num_dict[k2] -= i2[3]
                            product_amount_dict[k2] -= i2[4]
                        else:
                            product_num_dict[k2] = -i2[3]
                            product_amount_dict[k2] = -i2[4]
                            product_list.append(k2)
            if product_list:
                for j in product_list:
                    if product_num_dict.get(j, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                    data = {
                        'period_id': j[3],
                        'product_id': j[0],
                        'default_code': j[1],
                        'product_qty': product_num_dict.get(j, 0),
                        'price_unit': price_unit,
                        'product_amount': product_amount_dict.get(j, 0),
                        'uom_id': j[2],
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
        # # 季度查询
        elif int(self.search_choice) == 2:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                 'qdodoo_purchase_price_report_tree3')
            search_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                     'qdodoo_purchase_price_report_search3')
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
                    if ye.name not in name_year_list:
                        name_year_list.append(ye.name)
            for n_year in list(set(name_year_list)):
                if int(self.quarter) == 1:
                    key = str(n_year) + "第一季度"
                    start_p = '01' + '/' + str(n_year)
                    end_p = '03' + '/' + str(n_year)
                    per_starts = per_obj.search([('name', '=', start_p)])
                    if per_starts:
                        quarter_start[key] = per_starts[0].date_start
                    per_stops = per_obj.search([('name', '=', end_p)])
                    if per_stops:
                        quarter_stop[key] = per_stops[0].date_stop
                    quarter_key.append(key)
                elif int(self.quarter) == 2:
                    key = str(n_year) + "第二季度"
                    start_p = '04' + '/' + str(n_year)
                    end_p = '06' + '/' + str(n_year)
                    per_starts = per_obj.search([('name', '=', start_p)])
                    if per_starts:
                        quarter_start[key] = per_starts[0].date_start
                    per_stops = per_obj.search([('name', '=', end_p)])
                    if per_stops:
                        quarter_stop[key] = per_stops[0].date_stop
                    quarter_key.append(key)

                elif int(self.quarter) == 3:
                    key = str(n_year) + "第三季度"
                    start_p = '07' + '/' + str(n_year)
                    end_p = '09' + '/' + str(n_year)
                    per_starts = per_obj.search([('name', '=', start_p)])
                    if per_starts:
                        quarter_start[key] = per_starts[0].date_start
                    per_stops = per_obj.search([('name', '=', end_p)])
                    if per_stops:
                        quarter_stop[key] = per_stops[0].date_stop
                    quarter_key.append(key)

                elif int(self.quarter) == 4:
                    key = str(n_year) + "第四季度"
                    start_p = '10' + '/' + str(n_year)
                    end_p = '12' + '/' + str(n_year)
                    per_starts = per_obj.search([('name', '=', start_p)])
                    if per_starts:
                        quarter_start[key] = per_starts[0].date_start
                    per_stops = per_obj.search([('name', '=', end_p)])
                    if per_stops:
                        quarter_stop[key] = per_stops[0].date_stop
                    quarter_key.append(key)
                else:
                    start_p1 = '01' + '/' + str(n_year)
                    end_p1 = '03' + '/' + str(n_year)
                    per_starts1 = per_obj.search([('name', '=', start_p1)])
                    key1 = str(n_year) + "第一季度"
                    if per_starts1:
                        quarter_start[key1] = per_starts1[0].date_start
                    per_stops1 = per_obj.search([('name', '=', end_p1)])
                    if per_stops1:
                        quarter_stop[key1] = per_stops1[0].date_stop
                    quarter_key.append(key1)
                    start_p2 = '04' + '/' + str(n_year)
                    end_p2 = '06' + '/' + str(n_year)
                    key2 = str(n_year) + "第二季度"
                    per_starts2 = per_obj.search([('name', '=', start_p2)])
                    if per_starts2:
                        quarter_start[key2] = per_starts2[0].date_start
                    per_stops2 = per_obj.search([('name', '=', end_p2)])
                    if per_stops2:
                        quarter_stop[key2] = per_stops2[0].date_stop
                    quarter_key.append(key2)
                    start_p3 = '07' + '/' + str(n_year)
                    end_p3 = '09' + '/' + str(n_year)
                    key3 = str(n_year) + "第三季度"
                    per_starts3 = per_obj.search([('name', '=', start_p3)])
                    if per_starts3:
                        quarter_start[key3] = per_starts3[0].date_start
                    per_stops3 = per_obj.search([('name', '=', end_p3)])
                    if per_stops3:
                        quarter_stop[key3] = per_stops3[0].date_stop
                    quarter_key.append(key3)
                    start_p4 = '10' + '/' + str(n_year)
                    end_p4 = '12' + '/' + str(n_year)
                    key4 = str(n_year) + "第四季度"
                    per_starts4 = per_obj.search([('name', '=', start_p4)])
                    if per_starts4:
                        quarter_start[key4] = per_starts4[0].date_start
                    per_stops4 = per_obj.search([('name', '=', end_p4)])
                    if per_stops4:
                        quarter_stop[key4] = per_stops4[0].date_stop
                    quarter_key.append(key4)
            for d in quarter_key:
                sql_domain2 = copy.deepcopy(sql_domain)
                sql_where_base2 = sql_where_base
                sql_where_base2 = sql_where_base2 + " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s'"
                sql_domain2.append(quarter_start.get(d))
                sql_domain2.append(quarter_stop.get(d))
                sql_l1 = sql_select_base + sql_from_base + sql1_from_base + sql_where_base2
                sql_l2 = sql_select_base + sql_from_base + sql2_from_base + sql_where_base2 + " and ai.type = 'in_refund'"
                sql1 = sql_l1 % tuple(sql_domain2)
                self.env.cr.execute(sql1)
                res = self.env.cr.fetchall()
                if res:
                    for i in res:
                        # (产品，编码，单位，季度)
                        k = (i[1], i[2], i[5], d)
                        if k in product_list:
                            product_num_dict[k] += i[3]
                            product_amount_dict[k] += i[4]
                        else:
                            product_num_dict[k] = i[3]
                            product_amount_dict[k] = i[4]
                            product_list.append(k)
                sql2 = sql_l2 % tuple(sql_domain2)
                self.env.cr.execute(sql2)
                res2 = self.env.cr.fetchall()
                if res2:
                    for i2 in res2:
                        # (产品，编码，单位，季度)
                        k2 = (i2[1], i2[2], i2[5], d)
                        if k2 in product_list:
                            product_num_dict[k2] -= i2[3]
                            product_amount_dict[k2] -= i2[4]
                        else:
                            product_num_dict[k2] = -i2[3]
                            product_amount_dict[k2] = -i2[4]
                            product_list.append(k2)
            if product_list:
                for j in product_list:
                    if product_num_dict.get(j, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                    data = {
                        'quarter': j[3],
                        'product_id': j[0],
                        'default_code': j[1],
                        'product_qty': product_num_dict.get(j, 0),
                        'price_unit': price_unit,
                        'product_amount': product_amount_dict.get(j, 0),
                        'uom_id': j[2],
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
        # #####日期查询
        elif int(self.search_choice) == 3:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                 'qdodoo_purchase_price_report_tree4')
            search_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                     'qdodoo_purchase_price_report_search4')
            if self.date:
                sql_where_base = sql_where_base + " and ai.date_invoice = '%s'"
                sql_domain.append(self.date)
            sql_l1 = sql_select_base + sql_from_base + sql1_from_base + sql_where_base
            sql_l2 = sql_select_base + sql_from_base + sql2_from_base + sql_where_base + " and ai.type = 'in_refund'"
            sql1 = sql_l1 % tuple(sql_domain)
            self.env.cr.execute(sql1)
            res = self.env.cr.fetchall()
            if res:
                for i in res:
                    # (产品，编码，单位，时间)
                    k = (i[1], i[2], i[5], i[0])
                    if k in product_list:
                        product_num_dict[k] += i[3]
                        product_amount_dict[k] += i[4]
                    else:
                        product_num_dict[k] = i[3]
                        product_amount_dict[k] = i[4]
                        product_list.append(k)
            sql2 = sql_l2 % tuple(sql_domain)
            self.env.cr.execute(sql2)
            res2 = self.env.cr.fetchall()
            if res2:
                for i2 in res2:
                    # (产品，编码，单位，时间)
                    k2 = (i2[1], i2[2], i2[5], i2[0])
                    if k2 in product_list:
                        product_num_dict[k2] -= i2[3]
                        product_amount_dict[k2] -= i2[4]
                    else:
                        product_num_dict[k2] = -i2[3]
                        product_amount_dict[k2] = -i2[4]
                        product_list.append(k2)
            if product_list:
                for j in product_list:
                    if product_num_dict.get(j, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                    data = {
                        'date': j[3],
                        'product_id': j[0],
                        'default_code': j[1],
                        'product_qty': product_num_dict.get(j, 0),
                        'price_unit': price_unit,
                        'product_amount': product_amount_dict.get(j, 0),
                        'uom_id': j[2]
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
        #####时间段查询
        else:
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                 'qdodoo_purchase_price_report_tree5')
            search_model, search_id = model_obj.get_object_reference('qdodoo_purchase_price_change_report2',
                                                                     'qdodoo_purchase_price_report_search5')
            sql_where_base = sql_where_base + " and ai.date_invoice >= '%s'"
            sql_domain.append(self.start_date)
            sql_where_base = sql_where_base + " and ai.date_invoice <= '%s'"
            sql_domain.append(self.end_date)
            sql_l1 = sql_select_base + sql_from_base + sql1_from_base + sql_where_base
            sql_l2 = sql_select_base + sql_from_base + sql2_from_base + sql_where_base + " and ai.type = 'in_refund'"
            sql1 = sql_l1 % tuple(sql_domain)
            self.env.cr.execute(sql1)
            res = self.env.cr.fetchall()
            if res:
                for i in res:
                    # (产品，编码，单位)
                    k = (i[1], i[2], i[5])
                    if k in product_list:
                        product_num_dict[k] += i[3]
                        product_amount_dict[k] += i[4]
                    else:
                        product_num_dict[k] = i[3]
                        product_amount_dict[k] = i[4]
                        product_list.append(k)
            sql2 = sql_l2 % tuple(sql_domain)
            self.env.cr.execute(sql2)
            res2 = self.env.cr.fetchall()
            if res2:
                for i2 in res2:
                    # (产品，编码，单位)
                    k2 = (i2[1], i2[2], i2[5])
                    if k2 in product_list:
                        product_num_dict[k2] -= i2[3]
                        product_amount_dict[k2] -= i2[4]
                    else:
                        product_num_dict[k2] = -i2[3]
                        product_amount_dict[k2] = -i2[4]
                        product_list.append(k2)
            if product_list:
                for j in product_list:
                    if product_num_dict.get(j, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_amount_dict.get(j, 0) / product_num_dict.get(j, 0)
                    data = {
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'product_id': j[0],
                        'default_code': j[1],
                        'product_qty': product_num_dict.get(j, 0),
                        'price_unit': price_unit,
                        'product_amount': product_amount_dict.get(j, 0),
                        'uom_id': j[2],
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
        if result_list:
            return {
                'name': _('采购价格表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.purchase.price.report',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', result_list)],
                'views': [(tree_id, 'tree')],
                'view_id': [tree_id],
                'search_view_id': [search_id]
            }
        else:
            raise except_orm(_(u'警告'), _(u'未查询到数据'))
