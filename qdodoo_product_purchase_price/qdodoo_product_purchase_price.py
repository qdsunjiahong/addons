# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import osv, fields
from datetime import datetime

class qdodoo_product_purchase_price(osv.osv):
    _inherit = 'product.product'
    _description = u'产品采购价格'

    def _get_product_price(self, cr, uid, ids, fields, arg, context=None):
        result = {}
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        for product_obj in self.browse(cr, uid, ids, context=context):
            result[product_obj.id] = {}
            supplierinfo_ids = supplierinfo_obj.search(cr, uid, [('product_id','=',product_obj.id)], order='sequence')
            if supplierinfo_ids:
                ids_obj = supplierinfo_obj.browse(cr, uid, supplierinfo_ids[0])
                partner_id = ids_obj.name
                result[product_obj.id]['partner_id_one'] = partner_id.id
                if ids_obj.pricelist_ids:
                    result[product_obj.id]['product_qty_tfs'] = ids_obj.pricelist_ids[0].min_quantity
                    result[product_obj.id]['product_price'] = ids_obj.pricelist_ids[0].price
                else:
                    result[product_obj.id]['product_qty_tfs'] = 1.0
                    result[product_obj.id]['product_price'] = self.pool.get('product.pricelist').price_get(cr, uid, [partner_id.property_product_pricelist_purchase.id],
                    product_obj.id, 1.0, partner_id.id, {
                        'uom': product_obj.uom_po_id.id,
                        'date': datetime.now(),
                        })[partner_id.property_product_pricelist_purchase.id]
            else:
                result[product_obj.id]['partner_id_one'] = ''
                result[product_obj.id]['product_qty_tfs'] = 1.0
                result[product_obj.id]['product_price'] = product_obj.price_get('standard_price')[product_obj.id]
        return result

    _columns = {
        'partner_id_one':fields.function(_get_product_price, type='many2one', relation='res.partner', string="供应商", multi='price'),
        'product_price':fields.function(_get_product_price, type='float', string='价格', multi='price'),
        'product_qty_tfs':fields.function(_get_product_price, type='float', string='数量', multi='price'),
    }