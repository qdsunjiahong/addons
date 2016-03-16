# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, osv, api, _, models
import logging

_logger = logging.getLogger(__name__)

class qdodoo_product_mrp_line_report(models.TransientModel):
    """
        展示报表数据
    """
    _name = 'qdodoo.product.mrp.line.report'

    name = fields.Char(u'产品')
    department = fields.Char(u'部门')
    qty = fields.Float(u'产量', digits=(16,4))
    price_unit = fields.Float(u'单份产值', digits=(16,4))
    price = fields.Float(u'产值',compute="_get_price", digits=(16,4))
    price_cost = fields.Float(u'单份原料成本',compute="_get_price_cost", digits=(16,4))
    month_money = fields.Float(u'原料消耗金额', digits=(16,4))

    def _get_price(self):
        for ids in self:
            ids.price = ids.qty * ids.price_unit

    def _get_price_cost(self):
        for ids in self:
            if ids.qty:
                ids.price_cost = ids.month_money / ids.qty