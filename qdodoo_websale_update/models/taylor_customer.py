# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import fields, osv

class taylor_customer(osv.Model):
    """
        在客户中添加出库仓库
        在生成采购订单时 直接设置仓库 为客户中的仓库
    """

    _inherit = 'res.partner'    # 继承客户数据模型

    _columns = {    # 定义字段
        'out_stock': fields.many2one('stock.warehouse','仓库'),
        'location_id': fields.many2one('stock.location', '出库库位'),
    }

    def change_out_stock_id(self, cr, uid, ids, out_stock, context=None):
        if out_stock:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, out_stock, context=context)
            return {'value': {'location_id': warehouse.lot_stock_id.id}}
        return {}





