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

class qdodoo_arrival_rate_report(osv.Model):
    """
        到货率报表
    """
    _name = 'qdodoo.arrival.rate.report'    # 模型名称
    _auto = False

    _columns = {    # 定义字段
        'date': fields.datetime(u'日期', readonly=True),
        'partner_id': fields.many2one('res.partner',u'供应商', readonly=True),
        'purchase_id': fields.many2one('purchase.order',u'采购单', readonly=True),
        'product_id': fields.many2one('product.product',u'产品', readonly=True),
        'order_num': fields.float(u'订货数量', readonly=True),
        'delivery_num': fields.float(u'送货数量', readonly=True),
        'delivery_nmu_rate': fields.float(u'数量到货率', readonly=True),
        'price': fields.float(u'单价', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'qdodoo_arrival_rate_report')
        cr.execute("""
            create or replace view qdodoo_arrival_rate_report as (
                select
                    pol.id as id,
                    po.partner_id as partner_id,
                    sp.date_done as date,
                    po.id as purchase_id,
                    pol.product_id as product_id,
                    pol.product_qty as order_num,
                    sum(sm.product_uom_qty) as delivery_num,
                    sum(sm.product_uom_qty)/pol.product_qty as delivery_nmu_rate,
                    pol.price_unit as price
                from  purchase_order_line pol
                    LEFT JOIN purchase_order po ON po.id = pol.order_id
                    LEFT JOIN stock_move sm ON sm.purchase_line_id = pol.id
                    LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                where pol.state='done'
                group by
                    pol.id, po.partner_id, sp.date_done, po.id, pol.product_qty,pol.product_id,
                    sm.product_uom_qty, pol.price_unit
        )""")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: