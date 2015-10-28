# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_purchase_price_change_report(models.Model):
    _name = 'purchase.price.change.report'

    product_name = fields.Char(string=u'产品')
    delivery_place = fields.Many2one('stock.location', string=u'交货地点')
    date_planned = fields.Datetime(string=u'订单日期')
    unit_price = fields.Float(string=u'单价', digits=(16, 4))
    company_id = fields.Many2one('res.company', string=u'公司')
    partner_id = fields.Many2one('res.partner', string=u'供应商')


class qdodoo_purchase_price_change_search(models.Model):
    _name = 'purchase.price.change.search'

    def _get_company_id(self):
        user_obj = self.env['res.users'].browse(self.env.uid)
        return user_obj.company_id.id

    date_start = fields.Date(string=u'开始日期', required=True)
    date_end = fields.Date(string=u'结束日期')
    company_id = fields.Many2one('res.company', string=u'公司', required=True, default=_get_company_id)

    @api.multi
    def action_search(self):
        datetime_start = self.date_start + " 00:00:01"
        if self.date_end:
            datetime_end = self.date_end + " 23:59:59"
            sql = """
                select
                    pp.name_template as product_name,
                    po.date_order as date_planned,
                    ail.price_unit as unit_price,
                    po.company_id as company_id,
                    po.partner_id as partner_id,
                    spt.default_location_dest_id as delivery_place
                from account_invoice_line ail
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                    LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                    LEFT JOIN product_product pp on pp.id=ail.product_id
                where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.date_order <= '%s' and po.company_id = %s
                group by
                    po.id,pp.name_template,po.date_order,ail.price_unit,spt.default_location_dest_id,po.company_id,po.partner_id,ai.id,ail.invoice_id,pir.invoice_id,pir.purchase_id,po.picking_type_id,spt.id,pp.id,ail.product_id,ai.state
                """ % (datetime_start, datetime_end, self.company_id.id)
        else:
            sql = """
                select
                    pp.name_template as product_name,
                    po.date_order as date_planned,
                    ail.price_unit as unit_price,
                    po.company_id as company_id,
                    po.partner_id as partner_id,
                    spt.default_location_dest_id as delivery_place
                from account_invoice_line ail
                    LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id
                    LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id=ai.id
                    LEFT JOIN purchase_order po ON po.id = pir.purchase_id
                    LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
                    LEFT JOIN product_product pp on pp.id=ail.product_id
                where po.state = 'done' and ai.state != 'cancel' and po.date_order >= '%s' and po.company_id = %s
                group by
                    po.id,pp.name_template,po.date_order,ail.price_unit,spt.default_location_dest_id,po.company_id,po.partner_id,ai.id,ail.invoice_id,pir.invoice_id,pir.purchase_id,po.picking_type_id,spt.id,pp.id,ail.product_id,ai.state
                """ % (datetime_start, self.company_id.id)
        self.env.cr.execute(sql)
        result = self.env.cr.fetchall()
        return_list = []
        if result:
            for result_line in result:
                product_name, date_planned, unit_price, company_id, partner_id, delivery_place = result_line
                data = {
                    'product_name': product_name,
                    'date_planned': date_planned,
                    'unit_price': unit_price,
                    'company_id': company_id,
                    'partner_id': partner_id,
                    'delivery_place': delivery_place
                }
                cre_obj = self.env['purchase.price.change.report'].create(data)
                return_list.append(cre_obj.id)
        view_model, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_report_purchase_price_change',
                                                                             'purchase_price_change_report_tree')
        return {
            'name': (u'采购价格变动表'),
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'purchase.price.change.report',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', return_list)],
            'views': [(view_id, 'tree')],
            'view_id': [view_id],
        }
