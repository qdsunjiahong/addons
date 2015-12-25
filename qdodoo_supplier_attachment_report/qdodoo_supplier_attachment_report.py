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

class qdodoo_supplier_attachment_report(models.Model):
    """
        供应商证件查询表
    """
    _name = 'qdodoo.supplier.attachment.report'    # 模型名称
    _description = 'qdodoo.supplier.attachment.report'    # 模型描述

    partner_id = fields.Many2one('res.partner',u'供应商名称')
    name = fields.Many2one('ir.attachment',u'证件名称')
    num = fields.Integer(u'证件数量')
    date_start = fields.Date(u'开始时间')
    date_end = fields.Date(u'结束时间')
    state = fields.Char(u'状态')
    user_id = fields.Many2one('res.users',u'责任人')
    overdue = fields.Selection([('yes',u'已过期'),('no',u'未过期')],u'是否过期')
