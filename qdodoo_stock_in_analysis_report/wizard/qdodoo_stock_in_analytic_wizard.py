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

    def _get_company_id(self):
        return self.env['res.users'].browse(self.env.uid).company_id.id

    search_choice = fields.Selection(((1, u'年度'), (2, u'季度'), (3, u'供应商'), (4, u'日期'), (5, u'时间段')),
                                     string=u'查询方式', required=True, default=5)
    company_id = fields.Many2one('res.company', string=u'公司', required=True)
    year = fields.Many2one('account.fiscalyear', string=u'会计年度', attrs={'required': [('search_choice', 'in', (1, 2))]})
    quarter = fields.Selection(((1, 1), (2, 2), (3, 3), (4, 4)), string=u'季度',
                               attrs={'required': [('search_choice', '=', 2)]})
    partner_id = fields.Many2one('res.partner', string=u'供应商', attrs={'required': [('search_choice', '=', 3)]})
    date = fields.Date(string=u'日期', attrs={'required': [('search_choice', '=', 4)]})
    start_date = fields.Date(string=u'开始时间', attrs={'required': [('search_choice', '=', 5)]})
    end_date = fields.Date(string=u'结束时间', attrs={'required': [('search_choice', '=', 5)]})
    product_id = fields.Many2one('product.product', string=u'产品')

    @api.multi
    def action_done(self):
        report_obj = self.env['qdodoo.stock.in.analytic.report']
        result_list = []
        if self.company_id.name == u'惠美集团':
            if int(self.search_choice) == 1 and self.year:
                start_datetime = self.year.name + "-01-01 00:00:01"
                end_datetime = self.year.name + "-12-12 23:59:59"
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and pol.product_id = %s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.product_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done'
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime)
            elif int(self.search_choice) == 2 and self.year and self.quarter:
                if int(self.quarter) == 1:
                    start_datetime = self.year.name + "-01-01 00:00:01"
                    end_datetime = self.year.name + '-03-31 23:59:59'
                elif int(self.quarter) == 2:
                    start_datetime = self.year.name + '-04-01 00:00:01'
                    end_datetime = self.year.name + '-06-30 23:59:59'
                elif int(self.quarter) == 3:
                    start_datetime = self.year.name + '-07-01 00:00:01'
                    end_datetime = self.year.name + '-09-30 23:59:59'
                else:
                    start_datetime = self.year.name + '-10-01 00:00:01'
                    end_datetime = self.year.name + '-12-31 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and pol.product_id = %s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.product_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done'
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime)
            elif int(self.search_choice) == 3 and self.partner_id:
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.state = 'done' and pol.product_id = %s and po.partner_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state
                        """ % (self.product_id.id, self.partner_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.state = 'done' and po.partner_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state
                        """ % self.partner_id.id
            elif int(self.search_choice) == 4 and self.date:
                start_datetime = self.date + ' 00:00:01'
                end_datetime = self.date + ' 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and pol.product_id = %s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.product_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done'
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime)
            elif int(self.search_choice) == 5 and self.start_date and self.end_date:
                start_datetime = self.start_date + ' 00:00:01'
                end_datetime = self.end_date + ' 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and pol.product_id = %s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.product_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done'
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime)
            else:
                raise except_orm(_(u'警告'), _(u'请检查您的查询条件'))
        else:
            if int(self.search_choice) == 1 and self.year:
                start_datetime = self.year.name + "-01-01 00:00:01"
                end_datetime = self.year.name + "-12-12 23:59:59"
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and pol.product_id = %s and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.product_id.id, self.company_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.company_id.id)
            elif int(self.search_choice) == 2 and self.year and self.quarter:
                if int(self.quarter) == 1:
                    start_datetime = self.year.name + "-01-01 00:00:01"
                    end_datetime = self.year.name + '-03-31 23:59:59'
                elif int(self.quarter) == 2:
                    start_datetime = self.year.name + '-04-01 00:00:01'
                    end_datetime = self.year.name + '-06-30 23:59:59'
                elif int(self.quarter) == 3:
                    start_datetime = self.year.name + '-07-01 00:00:01'
                    end_datetime = self.year.name + '-09-30 23:59:59'
                else:
                    start_datetime = self.year.name + '-10-01 00:00:01'
                    end_datetime = self.year.name + '-12-31 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and pol.product_id = %s and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.product_id.id, self.company_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.company_id.id)
            elif int(self.search_choice) == 3 and self.partner_id:
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.state = 'done' and pol.product_id = %s and po.partner_id=%s and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state
                        """ % (self.product_id.id, self.partner_id.id, self.company_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.state = 'done' and po.partner_id=%s and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state
                        """ % (self.partner_id.id, self.company_id.id)
            elif int(self.search_choice) == 4 and self.date:
                start_datetime = self.date + ' 00:00:01'
                end_datetime = self.date + ' 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and pol.product_id = %s and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.product_id.id, self.company_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.company_id.id)
            elif int(self.search_choice) == 5 and self.start_date and self.end_date:
                start_datetime = self.start_date + ' 00:00:01'
                end_datetime = self.end_date + ' 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit),
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and pol.product_id = %s and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.product_id.id, self.company_id.id)
                else:
                    sql = """
                        select
                            po.partner_id as partner_id,
                            pol.product_id as product_id,
                            pol.product_qty as product_qty,
                            po.company_id as company_id,
                            (pol.product_qty * pol.price_unit) as product_amount,
                            pp.default_code,
                            po.location_id as location_id
                        from purchase_order_line pol
                            left join purchase_order po on po.id=pol.order_id
                            left join product_product pp on pp.id=pol.product_id
                        where po.date_order >= '%s' and po.date_order <= '%s' and po.state = 'done' and po.company_id=%s
                        group by po.partner_id,po.location_id,pol.product_id,pol.product_qty,pol.price_unit,pp.default_code,po.id,pol.order_id,pp.id,po.state,po.date_order
                        """ % (start_datetime, end_datetime, self.company_id.id)
            else:
                raise except_orm(_(u'警告'), _(u'请检查您的查询条件'))

        self.env.cr.execute(sql)
        res = self.env.cr.fetchall()
        product_list = []
        product_dict_amount = {}
        product_dict_num = {}
        if res:
            for i in res:
                k = (i[0], i[1], i[3], i[-2], i[-1])
                product_dict_amount[k] = product_dict_amount.get(k, 0) + i[4]
                product_dict_num[k] = product_dict_num.get(k, 0) + i[2]
                product_list.append(k)

        if product_list:
            for product_l in list(set(product_list)):
                data = {
                    'partner_id': product_l[0],
                    'code': product_l[3],
                    'product_id': product_l[1],
                    'product_qty': product_dict_num.get(product_l, 0),
                    'product_amount': product_dict_amount.get(product_l, 0),
                    'location_id': product_l[-1],
                    'company_id': product_l[2]
                }
                cre_obj = report_obj.create(data)
                result_list.append(cre_obj.id)
        if result_list:
            vie_mod, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_stock_in_analysis_report',
                                                                              'qdodoo_stock_in_analytic_report')
            return {
                'name': _('入库分析表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.stock.in.analytic.report',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', result_list)],
                'views': [(view_id, 'tree')],
                'view_id': [view_id],
            }
