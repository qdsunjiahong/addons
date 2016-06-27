# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:Qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, _, api, fields

class tms_trilateral_logistics(models.Model):
    """
        短驳基础数据
    """
    _name = 'tms.trilateral.logistics'

    name = fields.Char(u'名称')
    trilateral_add = fields.Float(u'短驳车加收费')
    location_id = fields.Many2one('stock.warehouse',u'物流中心')
    price_unit = fields.Float(u'起步价')
    warm_box = fields.Float(u'保温箱费用')
    other = fields.Float(u'其他费用')
    piece = fields.Float(u'费包用')
    is_specially = fields.Boolean(u'专线配送')
