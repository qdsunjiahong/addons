# encoding:utf-8

from openerp import models, api, _
from openerp.exceptions import except_orm


class qdodoo_product_template(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        res = super(qdodoo_product_template, self).create(vals)
        company_id = vals.get('company_id', False)
        if company_id:

            location_id = self.env['stock.location'].search(
                [('company_id', '=', company_id), ('usage', '=', 'inventory')])
            res.write({'property_stock_inventory': location_id})
        return res
