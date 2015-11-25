# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_purchase_price_report(models.Model):
    """
    采购价格变动表tree视图
    """
    _name = 'qdodoo.purchase.price.report'
    _description = 'qdodoo.purchase.price.report'
    _order = 'period_id'
    date = fields.Date(string=u'日期')
    year = fields.Char(string=u'年度')
    period_id = fields.Char(string=u'月份')
    quarter = fields.Char(string=u'季度')
    product_id = fields.Char(string=u'产品')
    default_code = fields.Char(string=u'产品编码')
    product_qty = fields.Float(string=u'数量')
    price_unit = fields.Float(string=u'单价', digits=(16, 4))
    start_date = fields.Date(string=u'开始时间')
    end_date = fields.Date(string=u'结束时间')
    uom_id = fields.Many2one('product.uom', string=u'单位')
