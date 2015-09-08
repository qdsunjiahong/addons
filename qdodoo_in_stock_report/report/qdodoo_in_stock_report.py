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

class qdodoo_in_stock_report(osv.Model):
    """
        入库明细表
    """
    _name = 'qdodoo.in.stock.report'    # 模型名称
    _auto = False

    _columns = {    # 定义字段
        'location_id': fields.many2one('stock.location',u'库位', readonly=True),
        'date': fields.datetime(u'日期', readonly=True),
        'partner_id': fields.many2one('res.partner',u'业务伙伴', readonly=True),
        'move_id': fields.many2one('stock.picking',u'单号', readonly=True),
        'product_id': fields.many2one('product.product',u'产品', readonly=True),
        'uom_id': fields.many2one('product.uom',u'单位', readonly=True),
        'product_qty': fields.float(u'数量', readonly=True),
        'price': fields.float(u'价格', readonly=True),
        'amount': fields.float(u'金额', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'qdodoo_in_stock_report')
        location_model, location_ids = self.pool.get('ir.model.data').get_object_reference(cr, SUPERUSER_ID, 'stock', 'stock_location_suppliers')
        location_model_cus, location_cus_ids = self.pool.get('ir.model.data').get_object_reference(cr, SUPERUSER_ID, 'stock', 'stock_location_customers')
        cr.execute("""
            create or replace view qdodoo_in_stock_report as (
                select
                    sm.id as id,
                    sm.location_dest_id as location_id,
                    sp.date_done as date,
                    sp.partner_id as partner_id,
                    sp.id as move_id,
                    sm.product_id as product_id,
                    sm.product_uom as uom_id,
                    sm.product_uom_qty as product_qty,
                    sm.price_unit as price,
                    (sm.price_unit * sm.product_uom_qty) as amount
                from stock_move sm
                    LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                    LEFT JOIN stock_location sl ON sm.location_id = sl.id
                where sm.state='done' and (sl.usage='transit' or sl.id=%s) and sm.location_dest_id != %s
                group by
                    sm.id, sm.location_dest_id, sm.product_id,sp.date_done,sp.id,sp.partner_id,
                    sm.price_unit, sm.product_uom_qty, sm.product_uom
        )"""% (location_ids,location_cus_ids))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: