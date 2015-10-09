# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_account_account_inherit(models.Model):
    _inherit = 'account.account'

    required_assistant = fields.Boolean(string=u'辅助核算想是否必填')


class qdodoo_sale_order(models.Model):
    _inherit = 'sale.order'

    def create(self, cr, uid, values, context=None):
        if values['order_line']:
            for line in values['order_line']:
                print line
                product_id = line[-1]['product_id']
                product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
                if product_obj.categ_id.property_stock_account_output_categ.required_assistant and not values[
                    'project_id']:
                    raise except_orm(_(u'警告'), _(u'辅助核算项必填！'))
                else:
                    return super(qdodoo_sale_order, self).create(cr, uid, values, context=context)
        else:
            return super(qdodoo_sale_order, self).create(cr, uid, values, context=context)

    @api.one
    def write(self, values):
        if not self.project_id and not values.get('project_id',[]):
            if self.order_line:
                for line in self.order_line:
                    if line.product_id.categ_id.property_stock_account_output_categ.required_assistant == True:
                        raise except_orm(_(u'警告'), _(u'辅助核算项必填！'))
                    else:
                        return super(qdodoo_sale_order, self).write(values)
            else:
                return super(qdodoo_sale_order, self).write(values)
        else:
            return super(qdodoo_sale_order, self).write(values)
