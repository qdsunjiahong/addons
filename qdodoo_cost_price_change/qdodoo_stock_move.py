# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_stock_move(models.Model):
    """
    继承调拨单，增加修改单价字段
    """
    _inherit = 'stock.move'

    change_price = fields.Float(string=u'单价调整')

    @api.multi
    def write(self, vals):
        if vals.get('change_price', False):
            change_price = vals.get('change_price')
            vals['price_unit'] = change_price
            res = super(qdodoo_stock_move, self).write(vals)
            product_id = self.product_id
            product_id.write({'standard_price': change_price})
            return res
        else:
            return super(qdodoo_stock_move, self).write(vals)

    def create(self, vals):
        if vals.get('change_price', False):
            change_price = vals.get('change_price')
            vals['price_unit'] = change_price
            res = super(qdodoo_stock_move, self).create(vals)
            res.product_id.write({'standard_price': change_price})
        else:
            return super(qdodoo_stock_move, self).create(vals)
