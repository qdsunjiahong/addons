# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import osv, fields
import datetime
import urllib2
from lxml import etree
from openerp.tools.translate import _


class qdodoo_hr_employee(osv.Model):
    """
        库存周转率
    """
    _inherit = 'hr.employee'

    # 字段定义
    _columns = {
        'work_data':fields.many2one("res.partner",'工作日志'),
    }
