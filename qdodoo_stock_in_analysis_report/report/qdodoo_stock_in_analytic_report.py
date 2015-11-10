# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_stock_in_analytic_report(models.Model):
    """
    入库分析表
    """
    _name = 'qdodoo.stock.in.analytic.report'
    _description = 'qdodoo.stock.in.analytic.report'

    partner_id = fields.Many2one('res.partner', string=u'供应商')
    code = fields.Char(string=u'产品编码')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_qty = fields.Float(digits=(16, 4), string=u'数量')
    product_amount = fields.Float(digits=(16, 4), string=u'金额')
    location_id = fields.Many2one('stock.location', string=u'库位')
    company_id=fields.Many2one('res.company',string=u'公司')
