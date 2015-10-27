# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_stock_in_report(models.Model):
    _name = 'qdodoo.stock.in.report'

    partner_id = fields.Many2one('res.partner', string=u'供应商')
    code = fields.Char(string=u'产品编码')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_qty = fields.Float(digits=(16, 4), string=u'数量')
    product_amount = fields.Float(digits=(16, 4), string=u'金额')
    location_id = fields.Many2one('stock.location', string=u'库位')


class qdodoo_search_stock_in(models.Model):
    _name = 'qdodoo.search.stock.in'

    date_start = fields.Date(string=u'开始时间')
    date_end = fields.Date(string=u'结束时间')
    location_id = fields.Many2one('stock.location', string=u'库位', required=True)

    @api.multi
    def action_done(self):
        purchase_obj = self.env['purchase.order']
        if self.date_start and not self.date_end:
            datetime_start = self.date_start + " 00:00:01"
            purchase_ids = purchase_obj.search([('date_order', '>=', datetime_start), ('state', '=', 'done'),
                                                ('location_id', '=', self.location_id.id)])
        elif not self.date_start and self.date_end:
            datetime_end = self.date_end + " 23:59:59"
            purchase_ids = purchase_obj.search(
                [('date_order', '<=', datetime_end), ('state', '=', 'done'), ('location_id', '=', self.location_id.id)])
        elif self.date_start and self.date_end:
            datetime_start = self.date_start + " 00:00:01"
            datetime_end = self.date_end + " 23:59:59"
            purchase_ids = purchase_obj.search(
                [('date_order', '>=', datetime_start), ('date_order', '<=', datetime_end), ('state', '=', 'done'),
                 ('location_id', '=', self.location_id.id)])
        else:
            purchase_ids = purchase_obj.search([('state', '=', 'done'), ('location_id', '=', self.location_id.id)])

        product_list = []
        product_dict = {}
        amount_dict = {}
        return_list = []
        if purchase_ids:
            for purchase_id in purchase_ids:
                for line in purchase_id.order_line:
                    if (line.product_id.id, line.order_id.partner_id.id) in product_list:
                        product_dict[(line.product_id.id, line.order_id.partner_id.id)] = product_dict.get(
                            (line.product_id.id, line.order_id.partner_id.id), 0.0) + line.product_qty
                        amount_dict[(line.product_id.id, line.order_id.partner_id.id)] = amount_dict.get(
                            (line.product_id.id, line.order_id.partner_id.id), 0.0) + line.price_subtotal
                    else:
                        product_dict[(line.product_id.id, line.order_id.partner_id.id)] = line.product_qty
                        amount_dict[(line.product_id.id, line.order_id.partner_id.id)] = line.price_subtotal
                        product_list.append((line.product_id.id, line.order_id.partner_id.id))
        for pro_l in product_list:
            data = {
                'partner_id': pro_l[1],
                'code': self.env['product.product'].browse(pro_l[0]).default_code,
                'product_id': pro_l[0],
                'product_qty': product_dict.get(pro_l, 0.0),
                'product_amount': amount_dict.get(pro_l, 0.0),
                'location_id': self.location_id.id

            }
            create_obj = self.env['qdodoo.stock.in.report'].create(data)
            return_list.append(create_obj.id)

        view_model, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_stock_in_report',
                                                                             'qdodoo_stock_in_report_tree')
        return {
            'name': _('入库分析表'),
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'qdodoo.stock.in.report',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', return_list)],
            'views': [(view_id, 'tree')],
            'view_id': [view_id],
        }
