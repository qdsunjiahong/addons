# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:Qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, _, api, fields

class tms_res_partner(models.Model):
    """
        线路信息
    """
    _inherit = 'res.partner'

    tms_location_id = fields.Many2one('stock.warehouse',u'物流中心')
    portal_plus = fields.Float(u'单店加收费')
    warm_box = fields.Float(u'保温箱费用')
    tms_other = fields.Float(u'其他费用')
    tms_piece = fields.Float(u'件费用')
    return_warm_box = fields.Float(u'回箱费用')
