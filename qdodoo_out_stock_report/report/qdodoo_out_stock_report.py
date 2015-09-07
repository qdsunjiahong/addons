# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import fields, osv
import time
from openerp import tools
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_out_stock_report(osv.Model):
    """
        出库明细表
    """
    _name = 'qdodoo.out.stock.report'    # 模型名称
    _auto = False

    _columns = {    # 定义字段
        'location_id': fields.many2one('stock.location',u'库位', readonly=True),
        'date': fields.datetime(u'日期', readonly=True),
        'partner_id': fields.many2one('res.partner',u'业务伙伴', readonly=True),
        'default_code': fields.char(u'编号', readonly=True),
        'product_id': fields.many2one('product.product',u'产品', readonly=True),
        'uom_id': fields.many2one('product.uom',u'单位', readonly=True),
        'product_qty': fields.float(u'数量', readonly=True),
        'price': fields.float(u'价格', readonly=True),
        'amount': fields.float(u'金额', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'qdodoo_out_stock_report')
        cr.execute("""
            create or replace view qdodoo_out_stock_report as (
                select
                    sm.id as id,
                    sm.location_id as location_id,
                    sm.date as date,
                    sm.partner_id as partner_id,
                    pp.default_code as default_code,
                    sm.product_id as product_id,
                    sm.product_uom as uom_id,
                    sm.product_uom_qty as product_qty,
                    sm.price_unit as price,
                    (sm.price_unit * sm.product_uom_qty) as amount
                from stock_move sm
                    LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                    LEFT JOIN product_product pp ON pp.id = sm.product_id
                where sm.state='done'
                group by
                    sm.id, sm.location_id, sm.partner_id, pp.default_code, sm.product_id,
                    sm.price_unit, sm.product_uom_qty, sm.product_uom
        )""")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: