# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_stock_inventory_report(models.Model):
    _name = 'qdodoo.stock.inventory.report2'

    mo_id = fields.Many2one('mrp.production', string=u'生产单')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_qty = fields.Float(digits=(16, 4), string=u'数量')
    inventory_id = fields.Many2one('stock.inventory', string=u'盘点单')
    date = fields.Date(string=u'盘点时间')
