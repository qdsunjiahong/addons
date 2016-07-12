# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class qdodoo_stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'
    # 退货时根据原单据是否有业务伙伴确定退货的开票状态,有业务伙伴则开票。
    def default_get(self, cr, uid, fields, context=None):
        res = super(qdodoo_stock_return_picking, self).default_get(cr, uid, fields, context=context)

        record_id = context and context.get('active_id', False) or False
        picking = self.pool.get('stock.picking').browse(cr, uid, record_id, context=context)
        if picking.partner_id:
            res['invoice_state'] = '2binvoiced'

        return res