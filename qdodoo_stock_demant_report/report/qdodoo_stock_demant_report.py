# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_stock_demant_report(models.Model):
    """
    内部调拨转移差异报表视图模型
    """
    _name = 'qdodoo.stock.demant.report'
    _description = 'qdodoo.stock.demant.report'

    sd_id=fields.Many2one('qdodoo.stock.demand',string=u'需求转换单')
    location_id = fields.Many2one('stock.location', string=u'源库位')
    qty_out = fields.Float(string=u'出库数量')
    location_dest_id = fields.Many2one('stock.location', string=u'目的库位')
    qty_in = fields.Float(string=u'入库数量')
    dif = fields.Float(string=u'差异数量')
    company_id = fields.Many2one('res.company', string=u'公司')
