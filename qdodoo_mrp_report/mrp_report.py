# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp import tools


class mrp_report_of_rain(osv.osv):
    _name = "mrp.report.of.rain"
    _description = "MRP actual theory report qdodoo"
    _auto = False
    _columns = {
        'production_efficiency': fields.float(u'出成', digits=(16, 4)),
        'date_planned': fields.datetime(u'下单日期', readonly=True),
        'product_id': fields.many2one('product.product', u'原料', readonly=True),
        'production_id': fields.many2one('mrp.production', u'生产订单', readonly=True),
        'analytics_id': fields.many2one('account.analytic.plan.instance', u'辅助核算'),
        'actual_money': fields.float(u'实际金额', digits=(16, 4)),
        'actual_consumption_num': fields.float(u'实际数量', digits=(16, 4)),
        'actual_price': fields.float(u'实际单价', digits=(16, 4)),
        'theory_num': fields.float(u'理论数量', digits=(16, 4)),
        'theory_money': fields.float(u'理论金额', digits=(16, 4)),
        'difference_qty': fields.float(u'差异数量', digits=(16, 4)),
        'qdr': fields.float(u'数量分配率', digits=(16, 4)),
        'actual_collar_num': fields.float(u'实际领用数量', digits=(16, 4)),
        'actual_collar_money': fields.float(u'实际领用金额', digits=(16, 4)),
        # 'theory_price': fields.float(u'理论单价'),
    }
    _defaults = {
        'actual_collar_num': 0,
        'actual_collar_money': 0
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'mrp_report_of_rain')
        cr.execute("""
            create or replace view mrp_report_of_rain as (
                select
                    sm.id as id,
                    0 as actual_collar_num,
                    0 as actual_collar_money,
                    mp.analytic_account as analytics_id,
                    mbl.product_efficiency as production_efficiency,
                    (sm.price_unit * sm.product_uom_qty) as actual_money,
                    sm.product_uom_qty as actual_consumption_num,
                    ((sm.price_unit * sm.product_uom_qty)/mppl.product_qty) as actual_price,
                    mppl.product_qty as theory_num,
                    (mppl.product_qty*((sm.price_unit * sm.product_uom_qty) / sm.product_uom_qty)) as theory_money,
                    mp.date_planned as date_planned,
                    sm.product_id as product_id,
                    mp.id as production_id,
                    (sm.product_uom_qty - mppl.product_qty) as difference_qty,
                    ((sm.product_uom_qty - mppl.product_qty) / mppl.product_qty) as qdr
                from mrp_production mp
                    LEFT JOIN stock_move sm ON sm.raw_material_production_id = mp.id
                    LEFT JOIN mrp_production_product_line mppl ON mppl.production_id = mp.id and mppl.product_id = sm.product_id
                    LEFT JOIN mrp_bom_line mbl ON mbl.bom_id = mp.bom_id and sm.product_id = mbl.product_id
                where mp.state='done' and sm.product_uom_qty > 0 and mppl.product_qty > 0
                group by
                    sm.id, mp.date_planned,mbl.product_efficiency ,sm.product_id, mp.id, mp.state, sm.price_unit, sm.product_uom_qty,mppl.product_qty, mppl.product_id
        )""")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
