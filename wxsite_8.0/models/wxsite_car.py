# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
import xlrd,base64
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class qdodoo_wxsite_car(models.Model):
    _name = 'qdodoo.wxsite.car'

    name = fields.Many2one('product.template','产品')
    user_id = fields.Many2one('res.users',u'用户')
    number = fields.Integer(u'数量')

class qdodoo_print_list(models.Model):
   _name = 'qdodoo.print.list'

   name = fields.Char(u'信息')
   is_print = fields.Boolean(u'是否已打印')
