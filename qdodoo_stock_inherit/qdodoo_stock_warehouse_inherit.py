# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
import time
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_res_user_inherit(models.Model):
    """
        在用户中增加仓库
    """
    _inherit = 'res.users'    # 继承

    warehouse_id = fields.Many2many('stock.warehouse','user_warehouse_rel','user_id','warehouse_id',u'管理的仓库')

    def create(self, cr, uid, value, context=None):
        res_id = super(qdodoo_res_user_inherit, self).create(cr, uid, value, context=context)
        obj = self.browse(cr, uid, res_id)
        if value.get('warehouse_id'):
            for line in obj.warehouse_id:
                sql_select = "delete from warehouse_user_rel where user_id=%s"%obj.id
                cr.execute(sql_select)
                sql = """INSERT INTO warehouse_user_rel (user_id, warehouse_id) VALUES (%s, %s)"""%(obj.id, line.id)
                cr.execute(sql)
        return res_id

    def write(self, cr, uid, ids, value, context=None):
        super(qdodoo_res_user_inherit, self).write(cr, uid, ids, value, context=context)
        obj = self.browse(cr, uid, ids[0])
        if value.get('warehouse_id'):
            for line in obj.warehouse_id:
                sql_select = "delete from warehouse_user_rel where user_id=%s"%obj.id
                cr.execute(sql_select)
                sql = """INSERT INTO warehouse_user_rel (user_id, warehouse_id) VALUES (%s, %s)"""%(obj.id, line.id)
                cr.execute(sql)
        return True


class qdodoo_stock_warehouse_inherit(models.Model):
    """
        在仓库中增加管理者
    """
    _inherit = 'stock.warehouse'    # 继承

    owner_line = fields.Many2many('res.users','warehouse_user_rel','warehouse_id','user_id',u'所有者')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: