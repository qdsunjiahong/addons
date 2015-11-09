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
    _name = 'qdodoo.purchase.pricew.wizard'
    _description = 'qdodoo.purchase.pricew.wizard'

    def _get_company_id(self):
        return self.env['res.users'].browse(self.env.uid).company_id.id

    # company_id = fields.Many2one('res.company', string=u'公司', required=True, default=_get_company_id)
    search_choice = fields.Selection(((1, u'年度'), (2, u'季度'), (4, u'日期'), (5, u'时间段')),
                                     string=u'查询方式', required=True, default=5)
    company_id = fields.Many2one('res.company', string=u'公司', required=True)
    year = fields.Many2one('account.fiscalyear', string=u'会计年度', attrs={'required': [('search_choice', '=', 1)]})
    quarter = fields.Selection(((1, 1), (2, 2), (3, 3), (4, 4)), string=u'季度')
    date = fields.Date(string=u'日期')
    start_date = fields.Date(string=u'开始时间')
    end_date = fields.Date(string=u'结束时间')
    product_id = fields.Many2one('product.product', string=u'产品')

    @api.multi
    def action_done(self):
        report_obj = self.env['qdodoo.purchase.price.report']
        result_list = []
        if self.company_id.name != u'惠美集团':
            if int(self.search_choice) == 1 and self.year:
                start_datetime = self.year.name + "-01-01 00:00:01"
                end_datetime = self.year.name + "-12-12 23:59:59"
                if self.product_id:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (self.product_id.id, start_datetime, end_datetime, self.company_id.id)
                else:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
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
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (self.product_id.id, start_datetime, end_datetime, self.company_id.id)
                else:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (start_datetime, end_datetime, self.company_id.id)
            # elif int(self.search_choice) == 3 and self.period_id:
            #     print 11111
            #     start_datetime = self.period_id.date_start + ' 00:00:01'
            #     end_datetime = self.period_id.date_stop + ' 23:59:59'
            #     if self.product_id:
            #         sql = """
            #             select
            #                 ail.product_id as product_id,
            #                 ail.quantity as product_qty,
            #                 ail.price_unit as price_unit,
            #                 spt.default_location_dest_id as location_id,
            #                 po.partner_id as partner_id,
            #                 po.date_order as date,
            #                 po.company_id as company_id
            #             from account_invoice_line ail
            #                 LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
            #                 LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
            #                 LEFT JOIN purchase_order po ON po.id = pir.purchase_id
            #                 LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
            #             where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
            #             group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
            #             """ % (self.product_id.id, start_datetime, end_datetime, self.company_id.id)
            #     else:
            #         sql = """
            #         select
            #                 ail.product_id as product_id,
            #                 ail.quantity as product_qty,
            #                 ail.price_unit as price_unit,
            #                 spt.default_location_dest_id as location_id,
            #                 po.partner_id as partner_id,
            #                 po.date_order as date,
            #                 po.company_id as company_id
            #             from account_invoice_line ail
            #                 LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
            #                 LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
            #                 LEFT JOIN purchase_order po ON po.id = pir.purchase_id
            #                 LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
            #             where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
            #             group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
            #             """ % (start_datetime, end_datetime, self.company_id.id)
            elif int(self.search_choice) == 4 and self.date:
                start_datetime = self.date + ' 00:00:01'
                end_datetime = self.date + ' 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (self.product_id.id, start_datetime, end_datetime, self.company_id.id)
                else:
                    sql = """
                    select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (start_datetime, end_datetime, self.company_id.id)
            elif int(self.search_choice) == 5 and self.start_date and self.end_date:
                start_datetime = self.start_date + ' 00:00:01'
                end_datetime = self.end_date + ' 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (self.product_id.id, start_datetime, end_datetime, self.company_id.id)
                else:
                    sql = """
                    select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (start_datetime, end_datetime, self.company_id.id)
            else:
                raise except_orm(_(u'警告'), _(u'请检查您的查询条件'))
        else:
            if int(self.search_choice) == 1 and self.year:
                start_datetime = self.year.name + "-01-01 00:00:01"
                end_datetime = self.year.name + "-12-12 23:59:59"
                if self.product_id:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (self.product_id.id, start_datetime, end_datetime)
                else:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
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
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (self.product_id.id, start_datetime, end_datetime)
                else:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (start_datetime, end_datetime)
            # elif int(self.search_choice) == 3 and self.period_id:
            #     start_datetime = self.period_id.date_start + ' 00:00:01'
            #     end_datetime = self.period_id.date_stop + ' 23:59:59'
            #     if self.product_id:
            #         sql = """
            #             select
            #                 ail.product_id as product_id,
            #                 ail.quantity as product_qty,
            #                 ail.price_unit as price_unit,
            #                 spt.default_location_dest_id as location_id,
            #                 po.partner_id as partner_id,
            #                 po.date_order as date,
            #                 po.company_id as company_id
            #             from account_invoice_line ail
            #                 LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
            #                 LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
            #                 LEFT JOIN purchase_order po ON po.id = pir.purchase_id
            #                 LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
            #             where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
            #             group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
            #             """ % (self.product_id.id, start_datetime, end_datetime)
            #     else:
            #         sql = """
            #         select
            #                 ail.product_id as product_id,
            #                 ail.quantity as product_qty,
            #                 ail.price_unit as price_unit,
            #                 spt.default_location_dest_id as location_id,
            #                 po.partner_id as partner_id,
            #                 po.date_order as date,
            #                 po.company_id as company_id
            #             from account_invoice_line ail
            #                 LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
            #                 LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
            #                 LEFT JOIN purchase_order po ON po.id = pir.purchase_id
            #                 LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
            #             where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
            #             group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
            #             """ % (start_datetime, end_datetime)
            elif int(self.search_choice) == 4 and self.date:
                start_datetime = self.date + ' 00:00:01'
                end_datetime = self.date + ' 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (self.product_id.id, start_datetime, end_datetime)
                else:
                    sql = """
                    select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (start_datetime, end_datetime)
            elif int(self.search_choice) == 5 and self.start_date and self.end_date:
                start_datetime = self.start_date + ' 00:00:01'
                end_datetime = self.end_date + ' 23:59:59'
                if self.product_id:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and ail.product_id=%s
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (self.product_id.id, start_datetime, end_datetime)
                else:
                    sql = """
                        select
                            ail.product_id as product_id,
                            ail.quantity as product_qty,
                            ail.price_unit as price_unit,
                            spt.default_location_dest_id as location_id,
                            po.partner_id as partner_id,
                            po.date_order as date,
                            po.company_id as company_id
                        from account_invoice_line ail
                            LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                            LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                            LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                            LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                        where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s'
                        group by ail.product_id,ail.quantity,ail.price_unit,spt.default_location_dest_id,ai.id,ail.invoice_id,pir.invoice_id,po.id,pir.purchase_id,po.picking_type_id,spt.id,po.state,po.company_id,po.date_order
                        """ % (start_datetime, end_datetime)
            else:
                raise except_orm(_(u'警告'), _(u'请检查您的查询条件'))
        self.env.cr.execute(sql)
        res = self.env.cr.fetchall()
        if res:
            for i in res:
                data = {
                    'date': i[5],
                    'partner_id': i[4],
                    'product_id': i[0],
                    'product_qty': i[1],
                    'price_unit': i[2],
                    'location_id': i[3],
                    'company_id': i[6]
                }
                res_obj = report_obj.create(data)
                result_list.append(res_obj.id)
        if result_list:
            vie_mod, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_purchase_price_change_report',
                                                                              'qdodoo_purchase_price_report_tree')
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
