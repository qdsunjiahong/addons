# -*- coding: utf-8 -*-
###########################################################################################
#
# module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_sale_order_consolidation(models.Model):
    """
    销售单合并wizard
    """
    _name = 'qdodoo_sale_order_consolidation'
    _description = 'qdodoo_sale_order_consolidation'

    def _get_sale_ids(self):
        sale_ids = ''
        partner_list = []
        location_list = []
        context = self._context or {}
        if context.get('active_model', False) == 'sale.order':
            active_ids = context.get('active_ids', [])
            if len(active_ids) < 2:
                raise except_orm(_(u'警告'), _(u'选择的销售单数量不能小于2'))
            for i in self.env['sale.order'].browse(active_ids):
                if i.state != "draft":
                    raise except_orm(_(u'警告'), _(u'只能选择草稿状态的销售单'))
                sale_ids += str(i.id) + ";"
                partner_list.append(i.partner_id.id)
                location_list.append(i.warehouse_id.id)
        if len(list(set(partner_list))) > 1 or len(list(set(location_list))) > 1:
            raise except_orm(_(u'警告'), _(u'不能选择客户或者仓库不同的销售单'))
        return sale_ids[0:-1]

    sale_ids = fields.Char(string=u'订单ID', default=_get_sale_ids)

    @api.multi
    def action_done(self):
        sale_ids = self.sale_ids
        model_obj = self.env['ir.model.data']
        product_move = {}
        sale_obj = self.env['sale.order']
        sale_new_list = []
        if sale_ids:
            sale_list = sale_ids.split(";")
            sale_new_id = int(sale_list[0])
            # 取第一个销售单为参照物
            sale_new = sale_obj.browse(sale_new_id)
            if sale_new.order_line:
                for o_l in sale_new.order_line:
                    product_id = (o_l.product_id.id, o_l.price_unit)
                    if product_id in product_move:
                        product_move[product_id].write(
                            {'product_uom_qty': o_l.product_uom_qty + product_move[product_id].product_uom_qty})
                        o_l.unlink()
                    else:
                        product_move[product_id] = o_l
            for sa_l in sale_list[1:]:
                sale_new_list.append(int(sa_l))
            # 循环另外的销售单
            for sale_id in sale_obj.browse(sale_new_list):
                order_lines = sale_id.order_line
                if order_lines:
                    for order_line in order_lines:
                        product_key = (order_line.product_id.id, order_line.price_unit)
                        if product_key in product_move:
                            product_move[product_key].write({"product_uom_qty": order_line.product_uom_qty +
                                                                                product_move[
                                                                                    product_key].product_uom_qty})
                        else:
                            order_line.write({"order_id": sale_new_id})
                    sale_id.write({'state': 'cancel'})

            view_model, view_tree_id = model_obj.get_object_reference('sale', 'view_quotation_tree')
            view_model2, view_form_id = model_obj.get_object_reference('sale', 'view_order_form')
            return {
                'name': _('报价单'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', [sale_new_id])],
                'views': [(view_tree_id, 'tree'), (view_form_id, 'form')],
                'view_id': [view_tree_id],
            }
