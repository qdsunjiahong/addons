# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import fields, osv
import time
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class qdodoo_template(osv.Model):
    """
    定义一个可以被搜索的日期字段

    """
    _inherit = 'account.invoice.line'  # 继承

    def get_default_date(self, cr, uid, ids, field, arg, context=None):
        result = {}
        for session in self.browse(cr, uid, ids, context=context):
            result[session.id] = session.create_date
        return result

    _columns = {  # 定义字段
                  'date': fields.function(get_default_date, string=u'日期', type='datetime'),
                  }
