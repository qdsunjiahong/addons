# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_purchase_order(models.Model):
    _inherit = 'purchase.order'

    pricelist_related = fields.Many2one('product.pricelist', related='pricelist_id', string=u'供应商价格表')
