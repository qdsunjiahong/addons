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

class qdodoo_account_invoice_inherit(models.Model):
    """
        在发票的源单据中增加上采购单号或销售单号
    """
    _inherit = 'account.invoice'    # 继承

    def create(self, cr, uid, vals, context=None):
        if vals.get('origin','') and vals.get('group_ref'):
            vals['origin'] = vals.get('origin','') + ':' + vals.get('group_ref')
        return super(qdodoo_account_invoice_inherit, self).create(cr, uid, vals, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: