# encoding:utf-8

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_product_set(models.Model):
    _name = 'qdodoo.product.set'

    @api.multi
    def action_search(self):
        return_list = []
        for product_id in self.env['product.template'].search([]):
            company_list = [product_id.company_id.id, 7]
            if product_id.seller_ids:
                for sell_id in product_id.seller_ids:
                    if sell_id.name.company_id.id not in company_list:
                        return_list.append(product_id.id)

        tree_model, tree_id = self.env['ir.model.data'].get_object_reference('product', 'product_template_tree_view')
        form_model, form_id = self.env['ir.model.data'].get_object_reference('product', 'product_template_only_form_view')
        return {
            'name': _(u'产品'),
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', return_list)],
            'views': [(tree_id, 'tree'),(form_id,'form')],
            'view_id': [tree_id],
        }
