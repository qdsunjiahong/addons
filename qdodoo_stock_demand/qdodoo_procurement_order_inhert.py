# -*- coding: utf-8 -*-
###########################################################################################
#
# module name for OpenERP
# Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_procurement_order(models.Model):
    _inherit = 'procurement.order'
    stock_demand_number = fields.Char(u'转换单号')
