# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    unit_price2 = fields.Float(related='price_unit', string=u'单价')
