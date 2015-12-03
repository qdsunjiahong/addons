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
        # 存储展示数据模型
        report_obj = self.env['qdodoo.stock.in.analytic.report']
        search_ids = report_obj.search([])
        search_ids.unlink()
        supplier_ids = self.pool.get('res.partner').search(self.env.cr, self.env.uid,
                                                           ['|', '|', ('name', 'ilike', u'期初'),
                                                            ('name', 'ilike', u'前期'), '&',
                                                            ('is_internal_company', '=', True),
                                                            ('supplier', '=', True)])
        product_domain = self.pool.get('product.product').search(self.env.cr, self.env.uid, [('type', '!=', 'service')])
        model_obj = self.env['ir.model.data']
        result_list = []
        partner_dict = {}
        partner_ids = self.env['res.partner'].search([])
        for partner_id in partner_ids:
            partner_dict[partner_id.id] = partner_id.property_supplier_payment_term.name
        sql_domain = []
        sql_l = """
            select
                ai.date_invoice as date,
                pp.name_template as product_name,
                pp.default_code as default_code,
                sm.product_uom_qty as product_qty,
                sm.price_unit as price_unit,
                (sm.product_uom_qty * sm.price_unit) as product_amount,
                po.partner_id as partner_id,
                po.location_id as location_id,
                po.company_id as company_id,
                pt.uom_po_id as uom_id
            FROM stock_move sm
                LEFT JOIN purchase_order_line pol on pol.id = sm.purchase_line_id
                LEFT JOIN purchase_order po on po.id = pol.order_id
                LEFT JOIN product_product pp on pp.id = sm.product_id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                LEFT JOIN purchase_invoice_rel pir ON po.id = pir.purchase_id
                LEFT JOIN account_invoice ai on pir.invoice_id=ai.id and ai.state != 'cancel'
            where sm.state = 'done' and po.state = 'done'
            """
        if len(supplier_ids) == 1:
            sql_l = sql_l + " and po.partner_id != %s"
            sql_domain.append(supplier_ids[0])
        elif len(supplier_ids) > 1:
            sql_l = sql_l + " and po.partner_id not in %s"
            sql_domain.append(tuple(supplier_ids))
        if int(self.search_choice) == 1:
            if self.year:
                start_datetime = self.year.date_start
                end_datetime = self.year.date_stop
                sql_l = sql_l + " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s'"
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
                    print r
                    year = r[0][:4]
                    data = {
                        'year': year,
                        'date': r[0],
                        'product_id': r[1],
                        'default_code': r[2],
                        'product_qty': r[3],
                        'uom_id': r[-1],
                        'price_unit': r[4],
                        'product_amount': r[5],
                        'location_id': r[7],
                        'company_id': r[8],
                        'partner_id': r[6],
                        'property_supplier_payment_term': partner_dict.get(r[6], '')
                    }
                    cre_obj = report_obj.create(data)
                    result_list.append(cre_obj.id)
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
            else:
                raise except_orm(_(u'提示'), _(u'未查询到数据'))
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
                    k = (per_ids[0].date_start, per_ids[0].date_stop)
                    if per_ids:
                        per_list_time.append(k)
                        per_dict_time[k] = month_l + '/' + str(self.year.name)
                if per_list_time:
                    for per_time in per_list_time:
                        sql_l2 = sql_l
                        sql_domain2 = copy.deepcopy(sql_domain)
                        if self.product_id:
                            sql_l2 = sql_l2 + ' and sm.product_id = %s'
                            sql_domain2.append(self.product_id.id)
                        pro_l = []
                        if self.product_id2:
                            product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                            for pr in product_ids:
                                pro_l.append(pr.id)
                            if len(pro_l) > 1:
                                sql_l2 = sql_l2 + ' and sm.product_id in %s'
                                sql_domain2.append(tuple(pro_l))
                            elif len(pro_l) == 1:
                                sql_l2 = sql_l2 + ' and sm.product_id = %s'
                                sql_domain2.append(pro_l[0])
                        if self.partner_id:
                            sql_l2 = sql_l2 + ' and po.partner_id = %s'
                            sql_domain2.append(self.partner_id.id)
                        if self.company_id:
                            sql_l2 = sql_l2 + ' and po.company_id=%s'
                            sql_domain2.append(self.company_id.id)
                        sql_l2 = sql_l2 + " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s'"
                        sql_domain2.append(per_time[0])
                        sql_domain2.append(per_time[1])
                        sql = sql_l2 % tuple(sql_domain2)
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
                                    'uom_id': r[-1],
                                    'price_unit': r[4],
                                    'product_amount': r[5],
                                    'location_id': r[7],
                                    'company_id': r[8],
                                    'partner_id': r[6],
                                    'property_supplier_payment_term': partner_dict.get(r[6], '')
                                }
                                cre_obj2 = report_obj.create(data)
                                result_list.append(cre_obj2.id)
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
                per_ids = per_obj.search([('name', '=', str(self.month) + '/' + str(self.year.name))])
                if per_ids:
                    start_datetime = per_ids[0].date_start
                    end_datetime = per_ids[0].date_stop
                    sql_l = sql_l + " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s'"
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
                                'uom_id': r[-1],
                                'price_unit': r[4],
                                'product_amount': r[5],
                                'location_id': r[7],
                                'company_id': r[8],
                                'partner_id': r[6],
                                'property_supplier_payment_term': partner_dict.get(r[6], '')
                            }
                            cre_obj2 = report_obj.create(data)
                            result_list.append(cre_obj2.id)
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
                        else:
                            raise except_orm(_(u'提示'), _(u'未查询到数据'))
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
                        k = (per_ids[0].date_start, per_ids[0].date_stop)
                        if per_ids:
                            per_list_time.append(k)
                            per_dict_time[k] = str(self.month) + '/' + str(ye_l)
                if per_list_time:
                    for per_time in per_list_time:
                        sql_l2 = sql_l
                        sql_domain2 = copy.deepcopy(sql_domain)
                        if self.product_id:
                            sql_l2 = sql_l2 + ' and sm.product_id = %s'
                            sql_domain2.append(self.product_id.id)
                        pro_l = []
                        if self.product_id2:
                            product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                            for pr in product_ids:
                                pro_l.append(pr.id)
                            if len(pro_l) > 1:
                                sql_l2 = sql_l2 + ' and sm.product_id in %s'
                                sql_domain2.append(tuple(pro_l))
                            elif len(pro_l) == 1:
                                sql_l2 = sql_l2 + ' and sm.product_id = %s'
                                sql_domain2.append(pro_l[0])
                        if self.partner_id:
                            sql_l2 = sql_l2 + ' and po.partner_id = %s'
                            sql_domain2.append(self.partner_id.id)
                        if self.company_id:
                            sql_l2 = sql_l2 + ' and po.company_id=%s'
                            sql_domain2.append(self.company_id.id)
                        sql_l2 = sql_l2 + " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s'"
                        sql_domain2.append(per_time[0])
                        sql_domain2.append(per_time[1])
                        sql = sql_l2 % tuple(sql_domain2)
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
                                    'uom_id': r[-1],
                                    'price_unit': r[4],
                                    'product_amount': r[5],
                                    'location_id': r[7],
                                    'company_id': r[8],
                                    'partner_id': r[6],
                                    'property_supplier_payment_term': partner_dict.get(r[6], '')
                                }
                                cre_obj2 = report_obj.create(data)
                                result_list.append(cre_obj2.id)
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
                                k = (per_ids[0].date_start, per_ids[0].date_stop)
                                per_list_time.append(k)
                                per_dict_time[k] = month_l + '/' + str(ye_l)
                if per_list_time:
                    for per_time in per_list_time:
                        sql_l2 = sql_l
                        sql_domain2 = copy.deepcopy(sql_domain)
                        if self.product_id:
                            sql_l2 = sql_l2 + ' and sm.product_id = %s'
                            sql_domain2.append(self.product_id.id)
                        pro_l = []
                        if self.product_id2:
                            product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                            for pr in product_ids:
                                pro_l.append(pr.id)
                            if len(pro_l) > 1:
                                sql_l2 = sql_l2 + ' and sm.product_id in %s'
                                sql_domain2.append(tuple(pro_l))
                            elif len(pro_l) == 1:
                                sql_l2 = sql_l2 + ' and sm.product_id = %s'
                                sql_domain2.append(pro_l[0])
                        if self.partner_id:
                            sql_l2 = sql_l2 + ' and po.partner_id = %s'
                            sql_domain2.append(self.partner_id.id)
                        if self.company_id:
                            sql_l2 = sql_l2 + ' and po.company_id=%s'
                            sql_domain2.append(self.company_id.id)
                        sql_l2 = sql_l2 + " and ai.date_invoice >= '%s' and ai.date_invoice <= '%s'"
                        sql_domain2.append(per_time[0])
                        sql_domain2.append(per_time[1])
                        sql = sql_l2 % tuple(sql_domain2)
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
                                    'uom_id': r[-1],
                                    'price_unit': r[4],
                                    'product_amount': r[5],
                                    'location_id': r[7],
                                    'company_id': r[8],
                                    'partner_id': r[6],
                                    'property_supplier_payment_term': partner_dict.get(r[6], '')
                                }
                                cre_obj2 = report_obj.create(data)
                                result_list.append(cre_obj2.id)
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
            for q in quarter_key:
                sql_domain2 = copy.deepcopy(sql_domain)
                sql_l2 = sql_l
                if quarter_start.get(q, None) != None:
                    sql_l2 = sql_l2 + " and ai.date_invoice >= '%s'"
                    sql_domain2.append(quarter_start.get(q))
                if quarter_stop.get(q, None) != None:
                    sql_domain2.append(quarter_stop.get(q))
                    sql_l2 = sql_l2 + " and ai.date_invoice <= '%s'"
                if self.product_id:
                    sql_l2 = sql_l2 + ' and sm.product_id = %s'
                    sql_domain2.append(self.product_id.id)
                pro_l = []
                if self.product_id2:
                    product_ids = self.env['product.product'].search([('name', '=', self.product_id2.name)])
                    for pr in product_ids:
                        pro_l.append(pr.id)
                    if len(pro_l) > 1:
                        sql_l2 = sql_l2 + ' and sm.product_id in %s'
                        sql_domain2.append(tuple(pro_l))
                    elif len(pro_l) == 1:
                        sql_l2 = sql_l2 + ' and sm.product_id = %s'
                        sql_domain2.append(pro_l[0])
                if self.partner_id:
                    sql_l2 = sql_l2 + ' and po.partner_id = %s'
                    sql_domain2.append(self.partner_id.id)
                if self.company_id:
                    sql_l2 = sql_l2 + ' and po.company_id = %s'
                    sql_domain.append(self.company_id.id)
                sql = sql_l2 % tuple(sql_domain2)
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
                            'uom_id': r[-1],
                            'price_unit': r[4],
                            'product_amount': r[5],
                            'location_id': r[7],
                            'company_id': r[8],
                            'partner_id': r[6],
                            'property_supplier_payment_term': partner_dict.get(r[6], '')
                        }
                        cre_obj2 = report_obj.create(data)
                        result_list.append(cre_obj2.id)
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
            else:
                raise except_orm(_(u'提示'), _(u'未查找到数据'))
        #####日期查询
        elif int(self.search_choice) == 3:
            sql_l = sql_l + " and ai.date_invoice = '%s'"
            sql_domain.append(self.date)
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
                        'uom_id': r[-1],
                        'price_unit': r[4],
                        'product_amount': r[5],
                        'location_id': r[7],
                        'company_id': r[8],
                        'partner_id': r[6],
                        'property_supplier_payment_term': partner_dict.get(r[6], '')
                    }

                    cre_obj2 = report_obj.create(data)
                    result_list.append(cre_obj2.id)
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
                else:
                    raise except_orm(_(u'提示'), _(u'未查询到数据'))
        #####时间段查询
        elif int(self.search_choice) == 4:
            sql_l = sql_l + " and ai.date_invoice >= '%s'"
            sql_domain.append(self.start_date)
            sql_l = sql_l + " and ai.date_invoice <= '%s'"
            sql_domain.append(self.end_date)
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
                        'uom_id': r[-1],
                        'price_unit': r[4],
                        'product_amount': r[5],
                        'location_id': r[7],
                        'company_id': r[8],
                        'partner_id': r[6],
                        'property_supplier_payment_term': partner_dict.get(r[6], '')
                    }
                    cre_obj2 = report_obj.create(data)
                    result_list.append(cre_obj2.id)
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
                else:
                    raise except_orm(_(u'提示'), _(u'未查询到数据'))
