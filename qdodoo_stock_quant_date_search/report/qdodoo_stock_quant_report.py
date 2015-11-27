# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_stock_quant_report2(models.Model):
    """
    总库存查询报表
    """
    _name = 'qdodoo.stock.quant.report2'
    _description = 'qdodoo.stock.quant.report2'

    product_name = fields.Char(string=u'产品')
    product_default = fields.Char(string=u'编码')
    product_qty = fields.Float(string=u'数量')
    uom=fields.Char(string=u'单位')
    product_amount = fields.Float(string=u'金额', digits=(16, 4))
    price_unit = fields.Float(string=u'单价', digits=(16, 4))
