# -*- coding: utf-8 -*-
###########################################################################################
#
# module name for OpenERP
# Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields
from datetime import datetime


class qdodoo_procurement_order(models.Model):
    _inherit = 'procurement.order'
    stock_demand_number = fields.Char(u'转换单号')
    associate_number = fields.Char(u'关联单号')

    def create_associate_number(self, cr, uid):
        print datetime.now(),'111111111111111111'
        obj_ids = self.search(cr, uid, [('group_id','!=',False)])
        picking_obj = self.pool.get('stock.picking')
        # 查询所有同一采购组的库位移动
        dict_val = {}
        picking_ids = picking_obj.search(cr, uid, [('group_id','!=',False)])
        for picking_id in picking_obj.browse(cr, uid, picking_ids):
            if picking_id.group_id.id in dict_val:
                dict_val[picking_id.group_id.id] += (';' + picking_id.name)
            else:
                dict_val[picking_id.group_id.id] = picking_id.name
        print datetime.now(),'3333333333333333333'
        for line in self.browse(cr, uid, obj_ids):
            self.write(cr, uid, [line.id], {'associate_number':dict_val.get(line.group_id.id)})
        print datetime.now(),'2222222222222222222222222'
        return True