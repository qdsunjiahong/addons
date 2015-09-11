# -*- coding: utf-8 -*-
from openerp import models,api,_,fields
###############
#
###############
import sys
reload(sys)

sys.setdefaultencoding('utf8')

class rainsoft_purchase_order(models.Model):
    _inherit ="purchase.order"

    deal_date = fields.Datetime(string="Deal Date")
    sum_qty = fields.Integer(string=u"数量合计",compute='_get_sum')
    item_qty = fields.Integer(string=u"条目合计",compute='_get_sum')

    @api.one
    def _get_sum(self):
        sum = 0
        for line in self.order_line:
            sum += line.product_qty
        self.sum_qty = sum
        self.item_qty = len(self.order_line)