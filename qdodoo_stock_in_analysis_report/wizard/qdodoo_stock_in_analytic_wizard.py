# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_stock_in_analytic_wizard(models.Model):
    """
    入库分析表wizard
    """
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
        supplier_id = self.env['res.partner'].search([('name', '=', u'前期库存'), ('active', '=', True)])[0].id
        search_ids = report_obj.search([])
        search_ids.unlink()
        model_obj = self.env['ir.model.data']
        result_list = []
        product_list_p = []
        product_dict_num = {}  # 数量
        product_dict_amount = {}  # 金额
        sql_l = """
            select
                sp.min_date as date,
                pp.name_template as product_name,
                pp.default_code as default_code,
                sm.product_uom_qty as product_qty,
                sm.price_unit as price_unit,
                (sm.product_uom_qty * sm.price_unit) as product_amount,
                po.partner_id as partner_id,
                po.location_id as location_id,
                po.company_id as company_id

            FROM stock_move sm
                LEFT JOIN stock_picking sp on sp.id = sm.picking_id
                LEFT JOIN purchase_order_line pol on pol.id = sm.purchase_line_id
                LEFT JOIN purchase_order po on po.id = pol.order_id
                LEFT JOIN res_partner rp on rp.id = po.partner_id
                LEFT JOIN product_product pp on pp.id = sm.product_id
            where sm.state = 'done' and sp.state = 'done' and po.state = 'done' and po.partner_id != %s
            """
        if int(self.search_choice) == 1:
            sql_domain = []
            sql_domain.append(supplier_id)
            if self.year:
                start_datetime = self.year.date_start + ' 00:00:01'
                end_datetime = self.year.date_stop + ' 23:59:59'
                sql_l = sql_l + " and sp.min_date >= '%s' and sp.min_date <= '%s'"
                sql_domain.append(start_datetime)
                sql_domain.append(end_datetime)
            if self.product_id:
                sql_l = sql_l + ' and sm.product_id = %s'
                sql_domain.append(self.product_id.id)
            pro_l = []
            if self.product_id2:
                product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                for pr in product_ids:
                    pro_l.append(pr.id)
                if len(pro_l) > 1:
                    sql_l = sql_l + ' and sm.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l) == 1:
                    sql_l = sql_l + ' and sm.product_id = %s'
                    sql_domain.append(pro_l[0])
            if self.partner_id:
                sql_l = sql_l + ' and po.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id:
                sql_l = sql_l + ' and po.company_id=%s'
                sql_domain.append(self.company_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                for r in res:
                    year = r[0][:4]
                    data = {
                        'year': year,
                        'date': r[0],
                        'product_id': r[1],
                        'default_code': r[2],
                        'product_qty': r[3],
                        'price_unit': r[4],
                        'product_amount': r[5],
                        'location_id': r[7],
                        'company_id': r[8],
                        'partner_id': r[6],
                        # 'property_supplier_payment_term': r[9]
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                    k = (year, r[1], r[2])
                    if k in product_list_p:
                        product_dict_num[k] += r[3]
                        product_dict_amount[k] += r[5]
                    else:
                        product_dict_num[k] = r[3]
                        product_dict_amount[k] = r[5]
                        product_list_p.append(k)
                for j in product_list_p:
                    if product_dict_num.get(j, 0) == 0:
                        price_u = 0
                    else:
                        price_u = product_dict_amount.get(j, 0) / product_dict_num.get(j, 0)
                    data2 = {
                        'year': j[0],
                        'product_id': j[1],
                        'product_qty': product_dict_num.get(j, 0),
                        'price_unit': price_u,
                        'product_amount': product_dict_amount.get(j, 0)
                    }
                    cre_obj2 = report_obj.create(data2)
                    result_list.append(cre_obj2.id)
            if result_list:
                vie_model, view_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                    'qdodoo_stock_in_analytic_report1')
                view_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                       'qdodoo_stock_in_analytic_search1')
                return {
                    'name': _('入库分析表'),
                    'view_type': 'form',
                    "view_mode": 'tree',
                    'res_model': 'qdodoo.stock.in.analytic.report',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', result_list)],
                    'views': [(view_id, 'tree')],
                    'view_id': [view_id],
                    'search_view_id': [search_id]
                }
        #####月份查询
        elif int(self.search_choice) == 5:
            per_obj = self.env['account.period']
            year_obj = self.env['account.fiscalyear']
            if self.year and not self.month:
                per_list_time = []
                per_dict_time = {}
                month_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
                for month_l in month_list:
                    per_ids = per_obj.search([('name', '=', month_l + '/' + str(self.year.name))])
                    k = (per_ids[0].date_start + ' 00:00:01', per_ids[0].date_stop + ' 23:59:59')
                    if per_ids:
                        per_list_time.append(k)
                        per_dict_time[k] = month_l + '/' + str(self.year.name)
                if per_list_time:
                    for per_time in per_list_time:
                        sql_l = """
                            select
                                sp.min_date as date,
                                pp.name_template as product_name,
                                pp.default_code as default_code,
                                sm.product_uom_qty as product_qty,
                                sm.price_unit as price_unit,
                                (sm.product_uom_qty * sm.price_unit) as product_amount,
                                po.partner_id as partner_id,
                                po.location_id as location_id,
                                po.company_id as company_id
                            FROM stock_move sm
                                LEFT JOIN stock_picking sp on sp.id = sm.picking_id
                                LEFT JOIN purchase_order_line pol on pol.id = sm.purchase_line_id
                                LEFT JOIN purchase_order po on po.id = pol.order_id
                                LEFT JOIN res_partner rp on rp.id = po.partner_id
                                LEFT JOIN product_product pp on pp.id = sm.product_id
                            where sm.state = 'done' and sp.state = 'done' and po.state = 'done' and po.partner_id != %s
                            """
                        sql_domain2 = []
                        sql_domain2.append(supplier_id)
                        if self.product_id:
                            sql_l = sql_l + ' and sm.product_id = %s'
                            sql_domain2.append(self.product_id.id)
                        pro_l = []
                        if self.product_id2:
                            product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                            for pr in product_ids:
                                pro_l.append(pr.id)
                            if len(pro_l) > 1:
                                sql_l = sql_l + ' and sm.product_id in %s'
                                sql_domain2.append(tuple(pro_l))
                            elif len(pro_l) == 1:
                                sql_l = sql_l + ' and sm.product_id = %s'
                                sql_domain2.append(pro_l[0])
                        if self.partner_id:
                            sql_l = sql_l + ' and po.partner_id = %s'
                            sql_domain2.append(self.partner_id.id)
                        if self.company_id:
                            sql_l = sql_l + ' and po.company_id=%s'
                            sql_domain2.append(self.company_id.id)
                        sql_l = sql_l + " and sp.min_date >= '%s' and sp.min_date <= '%s'"
                        sql_domain2.append(per_time[0])
                        sql_domain2.append(per_time[1])
                        sql = sql_l % tuple(sql_domain2)
                        self.env.cr.execute(sql)
                        res = self.env.cr.fetchall()
                        if res:
                            for r in res:
                                data = {
                                    'period_id': per_dict_time.get(per_time, ''),
                                    'date': r[0],
                                    'product_id': r[1],
                                    "default_code": r[2],
                                    'product_qty': r[3],
                                    'price_unit': r[4],
                                    'product_amount': r[5],
                                    'location_id': r[7],
                                    'company_id': r[8],
                                    'partner_id': r[6],
                                    # 'property_supplier_payment_term': r[9]
                                }
                                cre_obj2 = report_obj.create(data)
                                result_list.append(cre_obj2.id)
                                k = (per_dict_time.get(per_time, ''), r[1], r[2])
                                if k in product_list_p:
                                    product_dict_num[k] += r[3]
                                    product_dict_amount[k] += r[5]
                                else:
                                    product_dict_num[k] = r[3]
                                    product_dict_amount[k] = r[5]
                                    product_list_p.append(k)
                            for product_l in product_list_p:
                                if product_dict_num.get(product_l, 0) == 0:
                                    price_unit = 0
                                else:
                                    price_unit = product_dict_amount.get(product_l, 0) / product_dict_num.get(
                                        product_l,
                                        0)
                                data2 = {
                                    'period_id': product_l[0],
                                    'product_id': product_l[1],
                                    'default_code': product_l[2],
                                    'product_qty': product_dict_num.get(product_l, 0),
                                    'product_amount': product_dict_amount.get(product_l, 0),
                                    'price_unit': price_unit
                                }
                                cre_obj = report_obj.create(data2)
                                result_list.append(cre_obj.id)
                        else:
                            continue
                    if result_list:
                        vie_model, view_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                            'qdodoo_stock_in_analytic_report5')
                        view_model, search_id = model_obj.get_object_reference(
                            'qdodoo_stock_in_analysis_report',
                            'qdodoo_stock_in_analytic_search5')
                        return {
                            'name': _('入库分析表'),
                            'view_type': 'form',
                            "view_mode": 'tree',
                            'res_model': 'qdodoo.stock.in.analytic.report',
                            'type': 'ir.actions.act_window',
                            'domain': [('id', 'in', result_list)],
                            'views': [(view_id, 'tree')],
                            'view_id': [view_id],
                            'search_view_id': [search_id]
                        }
                    else:
                        raise except_orm(_(u'提示'), _(u'未查询到数据'))
            elif self.year and self.month:
                sql_domain = []
                sql_domain.append(supplier_id)
                per_ids = per_obj.search([('name', '=', str(self.month) + '/' + str(self.year.name))])
                if per_ids:
                    start_datetime = per_ids[0].date_start + ' 00:00:01'
                    end_datetime = per_ids[0].date_stop + ' 23:59:59'
                    sql_l = sql_l + " and sp.min_date >= '%s' and sp.min_date <= '%s'"
                    sql_domain.append(start_datetime)
                    sql_domain.append(end_datetime)
                    if self.product_id:
                        sql_l = sql_l + ' and sm.product_id = %s'
                        sql_domain.append(self.product_id.id)
                    pro_l = []
                    if self.product_id2:
                        product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                        for pr in product_ids:
                            pro_l.append(pr.id)
                        if len(pro_l) > 1:
                            sql_l = sql_l + ' and sm.product_id in %s'
                            sql_domain.append(tuple(pro_l))
                        elif len(pro_l) == 1:
                            sql_l = sql_l + ' and sm.product_id = %s'
                            sql_domain.append(pro_l[0])
                    if self.partner_id:
                        sql_l = sql_l + ' and po.partner_id = %s'
                        sql_domain.append(self.partner_id.id)
                    if self.company_id:
                        sql_l = sql_l + ' and po.company_id=%s'
                        sql_domain.append(self.company_id.id)
                    sql = sql_l % tuple(sql_domain)
                    self.env.cr.execute(sql)
                    res = self.env.cr.fetchall()
                    if res:
                        for r in res:
                            data = {
                                'period_id': str(self.month) + '/' + str(self.year.name),
                                'date': r[0],
                                'product_id': r[1],
                                "default_code": r[2],
                                'product_qty': r[3],
                                'price_unit': r[4],
                                'product_amount': r[5],
                                'location_id': r[7],
                                'company_id': r[8],
                                'partner_id': r[6],
                                # 'property_supplier_payment_term': r[9]
                            }
                            cre_obj2 = report_obj.create(data)
                            result_list.append(cre_obj2.id)
                            k = (r[0][:7], r[1], r[2])
                            if k in product_list_p:
                                product_dict_num[k] += r[3]
                                product_dict_amount[k] += r[5]
                            else:
                                product_dict_num[k] = r[3]
                                product_dict_amount[k] = r[5]
                                product_list_p.append(k)
                        for product_l in product_list_p:
                            if product_dict_num.get(product_l, 0) == 0:
                                price_unit = 0
                            else:
                                price_unit = product_dict_amount.get(product_l, 0) / product_dict_num.get(product_l, 0)
                            data2 = {
                                'period_id': product_l[0],
                                'product_id': product_l[1],
                                'default_code': product_l[2],
                                'product_qty': product_dict_num.get(product_l, 0),
                                'product_amount': product_dict_amount.get(product_l, 0),
                                'price_unit': price_unit
                            }
                            cre_obj = report_obj.create(data2)
                            result_list.append(cre_obj.id)
                        if result_list:
                            vie_model, view_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                                'qdodoo_stock_in_analytic_report5')
                            view_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                                   'qdodoo_stock_in_analytic_search5')
                            return {
                                'name': _('入库分析表'),
                                'view_type': 'form',
                                "view_mode": 'tree',
                                'res_model': 'qdodoo.stock.in.analytic.report',
                                'type': 'ir.actions.act_window',
                                'domain': [('id', 'in', result_list)],
                                'views': [(view_id, 'tree')],
                                'view_id': [view_id],
                                'search_view_id': [search_id]
                            }
            elif not self.year and self.month:
                ye_li = []
                year_ids = year_obj.search([])
                for year_id in year_ids:
                    ye_li.append(year_id.name)
                ye_li_new = list(set(ye_li))
                # 获取多年度某月的开始时间和结束时间
                per_list_time = []
                per_dict_time = {}
                if ye_li_new:
                    for ye_l in ye_li_new:
                        per_ids = per_obj.search([('name', '=', str(self.month) + '/' + str(ye_l))])
                        k = (per_ids[0].date_start + ' 00:00:01', per_ids[0].date_stop + ' 23:59:59')
                        if per_ids:
                            per_list_time.append(k)
                            per_dict_time[k] = str(self.month) + '/' + str(ye_l)
                if per_list_time:
                    for per_time in per_list_time:
                        sql_l = """
                            select
                                sp.min_date as date,
                                pp.name_template as product_name,
                                pp.default_code as default_code,
                                sm.product_uom_qty as product_qty,
                                sm.price_unit as price_unit,
                                (sm.product_uom_qty * sm.price_unit) as product_amount,
                                po.partner_id as partner_id,
                                po.location_id as location_id,
                                po.company_id as company_id

                            FROM stock_move sm
                                LEFT JOIN stock_picking sp on sp.id = sm.picking_id
                                LEFT JOIN purchase_order_line pol on pol.id = sm.purchase_line_id
                                LEFT JOIN purchase_order po on po.id = pol.order_id
                                LEFT JOIN res_partner rp on rp.id = po.partner_id
                                LEFT JOIN product_product pp on pp.id = sm.product_id
                            where sm.state = 'done' and sp.state = 'done' and po.state = 'done' and po.partner_id != %s
                            """
                        sql_domain2 = []
                        sql_domain2.append(supplier_id)
                        if self.product_id:
                            sql_l = sql_l + ' and sm.product_id = %s'
                            sql_domain2.append(self.product_id.id)
                        pro_l = []
                        if self.product_id2:
                            product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                            for pr in product_ids:
                                pro_l.append(pr.id)
                            if len(pro_l) > 1:
                                sql_l = sql_l + ' and sm.product_id in %s'
                                sql_domain2.append(tuple(pro_l))
                            elif len(pro_l) == 1:
                                sql_l = sql_l + ' and sm.product_id = %s'
                                sql_domain2.append(pro_l[0])
                        if self.partner_id:
                            sql_l = sql_l + ' and po.partner_id = %s'
                            sql_domain2.append(self.partner_id.id)
                        if self.company_id:
                            sql_l = sql_l + ' and po.company_id=%s'
                            sql_domain2.append(self.company_id.id)
                        sql_l = sql_l + " and sp.min_date >= '%s' and sp.min_date <= '%s'"
                        sql_domain2.append(per_time[0])
                        sql_domain2.append(per_time[1])
                        sql = sql_l % tuple(sql_domain2)
                        self.env.cr.execute(sql)
                        res = self.env.cr.fetchall()
                        if res:
                            per_ids2 = per_obj.search([('name', '=', str(self.month) + '/' + per_time[1][:4])])
                            if per_ids2:
                                per = per_ids2[0].name
                            for r in res:
                                data = {
                                    'period_id': per,
                                    'date': r[0],
                                    'product_id': r[1],
                                    "default_code": r[2],
                                    'product_qty': r[3],
                                    'price_unit': r[4],
                                    'product_amount': r[5],
                                    'location_id': r[7],
                                    'company_id': r[8],
                                    'partner_id': r[6],
                                    # 'property_supplier_payment_term': r[9]
                                }
                                cre_obj2 = report_obj.create(data)
                                result_list.append(cre_obj2.id)
                                k = (per, r[1], r[2])
                                if k in product_list_p:
                                    product_dict_num[k] += r[3]
                                    product_dict_amount[k] += r[5]
                                else:
                                    product_dict_num[k] = r[3]
                                    product_dict_amount[k] = r[5]
                                    product_list_p.append(k)
                            for product_l in product_list_p:
                                if product_dict_num.get(product_l, 0) == 0:
                                    price_unit = 0
                                else:
                                    price_unit = product_dict_amount.get(product_l, 0) / product_dict_num.get(
                                        product_l,
                                        0)
                                data2 = {
                                    'period_id': product_l[0],
                                    'product_id': product_l[1],
                                    'default_code': product_l[2],
                                    'product_qty': product_dict_num.get(product_l, 0),
                                    'product_amount': product_dict_amount.get(product_l, 0),
                                    'price_unit': price_unit
                                }
                                cre_obj = report_obj.create(data2)
                                result_list.append(cre_obj.id)
                        else:
                            continue
                    if result_list:
                        vie_model, view_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                            'qdodoo_stock_in_analytic_report5')
                        view_model, search_id = model_obj.get_object_reference(
                            'qdodoo_stock_in_analysis_report',
                            'qdodoo_stock_in_analytic_search5')
                        return {
                            'name': _('入库分析表'),
                            'view_type': 'form',
                            "view_mode": 'tree',
                            'res_model': 'qdodoo.stock.in.analytic.report',
                            'type': 'ir.actions.act_window',
                            'domain': [('id', 'in', result_list)],
                            'views': [(view_id, 'tree')],
                            'view_id': [view_id],
                            'search_view_id': [search_id]
                        }
                    else:
                        raise except_orm(_(u'提示'), _(u'未查询到数据'))
            else:
                ye_li = []
                year_ids = year_obj.search([])
                for year_id in year_ids:
                    ye_li.append(year_id.name)
                ye_li_new = list(set(ye_li))
                # 获取多年度某月的开始时间和结束时间
                per_list_time = []
                per_dict_time = {}
                month_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
                if ye_li_new:
                    for ye_l in ye_li_new:
                        for month_l in month_list:
                            per_ids = per_obj.search([('name', '=', month_l + '/' + str(ye_l))])
                            if per_ids:
                                k = (per_ids[0].date_start + ' 00:00:01', per_ids[0].date_stop + ' 23:59:59')
                                per_list_time.append(k)
                                per_dict_time[k] = month_l + '/' + str(ye_l)
                if per_list_time:
                    for per_time in per_list_time:
                        sql_l = """
                            select
                                sp.min_date as date,
                                pp.name_template as product_name,
                                pp.default_code as default_code,
                                sm.product_uom_qty as product_qty,
                                sm.price_unit as price_unit,
                                (sm.product_uom_qty * sm.price_unit) as product_amount,
                                po.partner_id as partner_id,
                                po.location_id as location_id,
                                po.company_id as company_id

                            FROM stock_move sm
                                LEFT JOIN stock_picking sp on sp.id = sm.picking_id
                                LEFT JOIN purchase_order_line pol on pol.id = sm.purchase_line_id
                                LEFT JOIN purchase_order po on po.id = pol.order_id
                                LEFT JOIN res_partner rp on rp.id = po.partner_id
                                LEFT JOIN product_product pp on pp.id = sm.product_id
                            where sm.state = 'done' and sp.state = 'done' and po.state = 'done' and po.partner_id != %s
                            """
                        sql_domain2 = []
                        sql_domain2.append(supplier_id)
                        if self.product_id:
                            sql_l = sql_l + ' and sm.product_id = %s'
                            sql_domain2.append(self.product_id.id)
                        pro_l = []
                        if self.product_id2:
                            product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                            for pr in product_ids:
                                pro_l.append(pr.id)
                            if len(pro_l) > 1:
                                sql_l = sql_l + ' and sm.product_id in %s'
                                sql_domain2.append(tuple(pro_l))
                            elif len(pro_l) == 1:
                                sql_l = sql_l + ' and sm.product_id = %s'
                                sql_domain2.append(pro_l[0])
                        if self.partner_id:
                            sql_l = sql_l + ' and po.partner_id = %s'
                            sql_domain2.append(self.partner_id.id)
                        if self.company_id:
                            sql_l = sql_l + ' and po.company_id=%s'
                            sql_domain2.append(self.company_id.id)
                        sql_l = sql_l + " and sp.min_date >= '%s' and sp.min_date <= '%s'"
                        sql_domain2.append(per_time[0])
                        sql_domain2.append(per_time[1])
                        sql = sql_l % tuple(sql_domain2)
                        self.env.cr.execute(sql)
                        res = self.env.cr.fetchall()
                        if res:
                            per2 = per_dict_time.get(per_time, '')
                            for r in res:
                                data = {
                                    'period_id': per2,
                                    'date': r[0],
                                    'product_id': r[1],
                                    "default_code": r[2],
                                    'product_qty': r[3],
                                    'price_unit': r[4],
                                    'product_amount': r[5],
                                    'location_id': r[7],
                                    'company_id': r[8],
                                    'partner_id': r[6],
                                    # 'property_supplier_payment_term': r[9]
                                }
                                cre_obj2 = report_obj.create(data)
                                result_list.append(cre_obj2.id)
                                k = (per2, r[1], r[2])
                                if k in product_list_p:
                                    product_dict_num[k] += r[3]
                                    product_dict_amount[k] += r[5]
                                else:
                                    product_dict_num[k] = r[3]
                                    product_dict_amount[k] = r[5]
                                    product_list_p.append(k)
                            for product_l in product_list_p:
                                if product_dict_num.get(product_l, 0) == 0:
                                    price_unit = 0
                                else:
                                    price_unit = product_dict_amount.get(product_l, 0) / product_dict_num.get(
                                        product_l,
                                        0)
                                data2 = {
                                    'period_id': product_l[0],
                                    'product_id': product_l[1],
                                    'default_code': product_l[2],
                                    'product_qty': product_dict_num.get(product_l, 0),
                                    'product_amount': product_dict_amount.get(product_l, 0),
                                    'price_unit': price_unit
                                }
                                cre_obj = report_obj.create(data2)
                                result_list.append(cre_obj.id)
                        else:
                            continue
                    if result_list:
                        vie_model, view_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                            'qdodoo_stock_in_analytic_report5')
                        view_model, search_id = model_obj.get_object_reference(
                            'qdodoo_stock_in_analysis_report',
                            'qdodoo_stock_in_analytic_search5')
                        return {
                            'name': _('入库分析表'),
                            'view_type': 'form',
                            "view_mode": 'tree',
                            'res_model': 'qdodoo.stock.in.analytic.report',
                            'type': 'ir.actions.act_window',
                            'domain': [('id', 'in', result_list)],
                            'views': [(view_id, 'tree')],
                            'view_id': [view_id],
                            'search_view_id': [search_id]
                        }
                    else:
                        raise except_orm(_(u'提示'), _(u'未查询到数据'))
        # 季度查询
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
                    key = (str(n_year) + "第一季度")
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
            for q in quarter_key:
                sql_domain = []
                sql_domain.append(supplier_id)
                if quarter_start.get(q, None) != None:
                    sql_l = sql_l + " and sp.min_date >= '%s'"
                    sql_domain.append(quarter_start.get(q))
                if quarter_stop.get(q, None) != None:
                    sql_domain.append(quarter_stop.get(q))
                    sql_l = sql_l + " and sp.min_date <= '%s'"
                if self.product_id:
                    sql_l = sql_l + ' and sm.product_id = %s'
                    sql_domain.append(self.product_id.id)
                pro_l = []
                if self.product_id2:
                    product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                    for pr in product_ids:
                        pro_l.append(pr.id)
                    if len(pro_l) > 1:
                        sql_l = sql_l + ' and sm.product_id in %s'
                        sql_domain.append(tuple(pro_l))
                    elif len(pro_l) == 1:
                        sql_l = sql_l + ' and sm.product_id = %s'
                        sql_domain.append(pro_l[0])
                if self.partner_id:
                    sql_l = sql_l + ' and po.partner_id = %s'
                    sql_domain.append(self.partner_id.id)
                if self.company_id:
                    sql_l = sql_l + ' and po.company_id = %s'
                    sql_domain.append(self.company_id.id)
                sql = sql_l % tuple(sql_domain)
                self.env.cr.execute(sql)
                res = self.env.cr.fetchall()
                if res:
                    for r in res:
                        data = {
                            'quarter': q,
                            'date': r[0],
                            'product_id': r[1],
                            "default_code": r[2],
                            'product_qty': r[3],
                            'price_unit': r[4],
                            'product_amount': r[5],
                            'location_id': r[7],
                            'company_id': r[8],
                            'partner_id': r[6],
                            # 'property_supplier_payment_term': r[9]
                        }
                        cre_obj2 = report_obj.create(data)
                        result_list.append(cre_obj2.id)
                        k = (q, r[0], r[1])
                        if k in product_list_p:
                            product_dict_num[k] += r[4]
                            product_dict_amount[k] += r[6]
                        else:
                            product_dict_num[k] = r[4]
                            product_dict_amount[k] = r[6]
                            product_list_p.append(k)
            if product_list_p:
                for product_l in product_list_p:
                    if product_dict_num.get(product_l, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_dict_amount.get(product_l, 0) / product_dict_num.get(product_l, 0)
                    data = {
                        'quarter': product_l[0],
                        'product_id': product_l[1],
                        'default_code': product_l[-1],
                        'price_unit': price_unit,
                        'product_qty': product_dict_num.get(product_l, 0),
                        'product_amount': product_dict_amount.get(product_l, 0),
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                if result_list:
                    vie_model, view_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                        'qdodoo_stock_in_analytic_report2')
                    view_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                           'qdodoo_stock_in_analytic_search2')
                    return {
                        'name': _('入库分析表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.stock.in.analytic.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                        'search_view_id': [search_id]
                    }
        #####日期查询
        elif int(self.search_choice) == 3:
            sql_domain = []
            sql_domain.append(supplier_id)
            start_datetime = self.date + ' 00:00:01'
            end_datetime = self.date + ' 23:59:59'
            sql_l = sql_l + " and sp.min_date >= '%s' and sp.min_date <= '%s'"
            sql_domain.append(start_datetime)
            sql_domain.append(end_datetime)
            if self.product_id:
                sql_l = sql_l + ' and sm.product_id = %s'
                sql_domain.append(self.product_id.id)
            pro_l = []
            if self.product_id2:
                product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                for pr in product_ids:
                    pro_l.append(pr.id)
                if len(pro_l) > 1:
                    sql_l = sql_l + ' and sm.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l) == 1:
                    sql_l = sql_l + ' and sm.product_id = %s'
                    sql_domain.append(pro_l[0])
            if self.partner_id:
                sql_l = sql_l + ' and po.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            if self.company_id:
                sql_l = sql_l + ' and po.company_id = %s'
                sql_domain.append(self.company_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                for r in res:
                    data = {
                        'date': r[0],
                        'product_id': r[1],
                        "default_code": r[2],
                        'product_qty': r[3],
                        'price_unit': r[4],
                        'product_amount': r[5],
                        'location_id': r[7],
                        'company_id': r[8],
                        'partner_id': r[6],
                        # 'property_supplier_payment_term': r[9]
                    }

                    cre_obj2 = report_obj.create(data)
                    result_list.append(cre_obj2.id)
                    k = (r[1], r[2])
                    if k in product_list_p:
                        product_dict_num[k] += r[3]
                        product_dict_amount[k] += r[5]
                    else:
                        product_dict_num[k] = r[3]
                        product_dict_amount[k] = r[5]
                        product_list_p.append(k)
                for product_l in product_list_p:
                    if product_dict_num.get(product_l, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_dict_amount.get(product_l, 0) / product_dict_num.get(product_l, 0)
                    data = {
                        'date': self.date,
                        'product_id': product_l[0],
                        'default_code': product_l[1],
                        'product_qty': product_dict_num.get(product_l, 0),
                        'price_unit': price_unit,
                        'product_amount': product_dict_amount.get(product_l, 0),
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                if result_list:
                    vie_model, view_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                        'qdodoo_stock_in_analytic_report3')
                    view_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                           'qdodoo_stock_in_analytic_search3')
                    return {
                        'name': _('入库分析表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.stock.in.analytic.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                        'search_view_id': [search_id]
                    }
        #####时间段查询
        elif int(self.search_choice) == 4:
            sql_domain = []
            sql_domain.append(supplier_id)
            sql_l = sql_l + " and sp.min_date >= '%s'"
            sql_domain.append(self.start_date + ' 00:00:01')
            sql_l = sql_l + " and sp.min_date <= '%s'"
            sql_domain.append(self.end_date + ' 23:59:59')
            if self.company_id:
                sql_l = sql_l + ' and po.company_id = %s'
                sql_domain.append(self.company_id.id)
            if self.product_id:
                sql_l = sql_l + 'and sm.product_id = %s'
                sql_domain.append(self.product_id.id)
            pro_l = []
            if self.product_id2:
                product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                for pr in product_ids:
                    pro_l.append(pr.id)
                if len(pro_l) > 1:
                    sql_l = sql_l + ' and sm.product_id in %s'
                    sql_domain.append(tuple(pro_l))
                elif len(pro_l) == 1:
                    sql_l = sql_l + ' and sm.product_id = %s'
                    sql_domain.append(pro_l[0])
            if self.partner_id:
                sql_l = sql_l + ' and po.partner_id = %s'
                sql_domain.append(self.partner_id.id)
            sql = sql_l % tuple(sql_domain)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                for r in res:
                    data = {
                        'date': r[0],
                        'product_id': r[1],
                        "default_code": r[2],
                        'product_qty': r[3],
                        'price_unit': r[4],
                        'product_amount': r[5],
                        'location_id': r[7],
                        'company_id': r[8],
                        'partner_id': r[6],
                        # 'property_supplier_payment_term': r[9]
                    }
                    cre_obj2 = report_obj.create(data)
                    result_list.append(cre_obj2.id)

                    k = (r[1], r[2])
                    if k in product_list_p:
                        product_dict_num[k] += r[3]
                        product_dict_amount[k] += r[5]
                    else:
                        product_dict_num[k] = r[3]
                        product_dict_amount[k] = r[5]
                        product_list_p.append(k)
                for product_l in product_list_p:
                    if product_dict_num.get(product_l, 0) == 0:
                        price_unit = 0
                    else:
                        price_unit = product_dict_amount.get(product_l, 0) / product_dict_num.get(product_l, 0)
                    data = {
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'product_id': product_l[0],
                        'default_code': product_l[1],
                        'product_qty': product_dict_num.get(product_l, 0),
                        'product_amount': product_dict_amount.get(product_l, 0),
                        'price_unit': price_unit,
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
                if result_list:
                    vie_model, view_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                        'qdodoo_stock_in_analytic_report3')
                    view_model, search_id = model_obj.get_object_reference('qdodoo_stock_in_analysis_report',
                                                                           'qdodoo_stock_in_analytic_search3')
                    return {
                        'name': _('入库分析表'),
                        'view_type': 'form',
                        "view_mode": 'tree',
                        'res_model': 'qdodoo.stock.in.analytic.report',
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', result_list)],
                        'views': [(view_id, 'tree')],
                        'view_id': [view_id],
                        'search_view_id': [search_id]
                    }
