# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_reverse_transfer(models.Model):
    """
    退货取采购单或销售单价格
    """
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        product_price_list = {}
        context = self._context or {}
        record_id = context and context.get('active_id', False) or False
        if not record_id:
            raise except_orm(_(u'警告'), _(u'移动单与采购单关联异常'))
        sale_obj = self.env['sale.order']
        picking_obj = self.env['stock.picking']
        code = picking_obj.browse(record_id).picking_type_id.code
        if code == "outgoing":
            picking_id = picking_obj.browse(record_id)
            sale_id = sale_obj.search([('procurement_group_id', '=', picking_id.group_id.id)])
            if not sale_id or len(sale_id) > 1:
                raise except_orm(_(u'警告'), _(u'销售单与移库蛋关联异常'))
            for move_l in sale_id.order_line:
                product_price_list[move_l.product_id.id] = move_l.price_unit
        elif code == 'incoming':
            query = """
                SELECT
                  po.id
                FROM stock_picking p,
                     stock_move m,
                     purchase_order_line pol,
                     purchase_order po
                WHERE p.id = %s and po.id = pol.order_id and pol.id = m.purchase_line_id and m.picking_id = p.id
                GROUP BY picking_id, po.id
            """ % record_id
            self.env.cr.execute(query)
            res = self.env.cr.fetchall()
            if res and len(res) == 1:
                purchase_id = self.env['purchase.order'].browse(res[0][0])
                if purchase_id.order_line:
                    for order_id in purchase_id.order_line:
                        product_price_list[order_id.product_id.id] = order_id.price_unit
        new_picking_id, pick_type_id = super(qdodoo_reverse_transfer, self)._create_returns()
        picking_id2 = picking_obj.browse(new_picking_id)
        if picking_id2.move_lines:
            for move_line in picking_id2.move_lines:
                product_id = move_line.product_id.id
                if product_id in product_price_list:
                    move_line.write({'price_unit': product_price_list.get(product_id)})
        return new_picking_id, pick_type_id
