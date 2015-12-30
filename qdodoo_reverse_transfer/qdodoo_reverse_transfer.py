# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp import SUPERUSER_ID


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
        purchase_obj = self.env['purchase.order']
        picking_obj = self.env['stock.picking']
        origin = picking_obj.browse(record_id).origin
        purchase_ids = purchase_obj.search([('name', '=', origin)])
        sale_ids = sale_obj.search([('name', '=', origin)])
        if sale_ids:
            for move_l in sale_ids.order_line:
                product_price_list[move_l.product_id.id] = move_l.price_unit
        elif purchase_ids:
            for order_id in purchase_ids.order_line:
                product_price_list[order_id.product_id.id] = order_id.price_unit
        new_picking_id, pick_type_id = super(qdodoo_reverse_transfer, self)._create_returns()
        picking_id2 = picking_obj.browse(new_picking_id)
        if picking_id2.move_lines:
            for move_line in picking_id2.move_lines:
                product_id = move_line.product_id.id
                if product_id in product_price_list:
                    move_line.write({'price_unit': product_price_list.get(product_id)})
        return new_picking_id, pick_type_id

class qdodoo_stock_move(models.Model):
    _inherit = "stock.move"

    def product_price_update_before_done(self, cr, uid, ids, context=None):
        super(qdodoo_stock_move, self).product_price_update_before_done(cr, uid, ids, context=context)
        product_obj = self.pool.get('product.product')
        tmpl_dict = {}
        for move in self.browse(cr, uid, ids, context=context):
            # 如果是采购反向转移
            if  (move.location_dest_id.usage == 'supplier') and (move.product_id.cost_method == 'average'):
                # 获取产品模板和产品数据模型
                product = move.product_id
                prod_tmpl_id = move.product_id.product_tmpl_id.id
                qty_available = move.product_id.product_tmpl_id.qty_available
                if tmpl_dict.get(prod_tmpl_id):
                    product_avail = qty_available + tmpl_dict[prod_tmpl_id]
                else:
                    tmpl_dict[prod_tmpl_id] = 0
                    product_avail = qty_available
                if product_avail <= 0:
                    new_std_price = move.price_unit
                else:
                    # Get the standard price
                    amount_unit = product.standard_price
                    new_std_price = ((amount_unit * product_avail) - (move.price_unit * move.product_qty)) / (product_avail - move.product_qty)
                tmpl_dict[prod_tmpl_id] += move.product_qty
                # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
                product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price}, context=context)
