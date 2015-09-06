# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models
import time
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_stock_warehouse_inherit(models.Model):
    """
        仓库所有者权限
    """
    _inherit = 'stock.warehouse'    # 继承

    owner_line = fields.Many2many('res.users','warehouse_id','user_id',u'所有者')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: