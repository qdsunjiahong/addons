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

    _order = 'period_id'
    date = fields.Date(string=u'日期')
    year = fields.Many2one('account.fiscalyear', string=u'年度')
    period_id = fields.Many2one('account.period', string=u'月份')
    quarter = fields.Char(string=u'季度')
    partner_id = fields.Many2one('res.partner', string=u'供应商')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_qty = fields.Float(string=u'数量')
    price_unit = fields.Float(string=u'单价', digits=(16, 4))
    product_amount = fields.Float(string=u'金额')
    location_id = fields.Many2one('stock.location', string=u'交货地点')
    company_id = fields.Many2one('res.company', string=u'公司')
