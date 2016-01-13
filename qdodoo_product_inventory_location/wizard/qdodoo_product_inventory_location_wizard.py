# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_product_inventory_location(models.Model):
    _name = 'qdodoo.product.inventory.location'
    _description = 'qdodoo.product.inventory.location'

    @api.multi
    def action_done(self):
        company_ids = self.env['res.users'].browse(self.env.uid).company_id
        company_id = company_ids.id
        location_obj = self.env['stock.location']
        location_ids = location_obj.search([('usage', '=', 'inventory'), ('company_id', '=', company_id)])
        if not location_ids:
            raise except_orm(_(u'警告'), _(u'公司"%s"未创建盘点类型库位') % company_ids.name)
        elif len(location_ids) > 1:
            raise except_orm(_(u'警告'), _(u'公司"%s"存在多个盘点类型库位') % company_ids.name)
        product_obj = self.env['product.template']
        product_ids = product_obj.search([('type', '!=', 'service'), ('company_id', '=', company_id)])

        result_list = []
        for product_id in product_ids:
            location_id1 = location_ids.id
            location_id2 = product_id.property_stock_inventory.id or ''
            if location_id1 != location_id2:
                product_id.write({'property_stock_inventory': location_id1})
                result_list.append(product_id.id)
        model_obj = self.env['ir.model.data']
        tree_mode, tree_id = model_obj.get_object_reference('product', 'product_template_tree_view')
        form_mode, form_id = model_obj.get_object_reference('product', 'product_template_only_form_view')
        return {
            'name': (u'修改过的产品'),
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', result_list)],
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'view_id': [tree_id]
        }
