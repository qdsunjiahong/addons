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

class qdodoo_mrp_actual_theory_wizard(osv.osv_memory):
    """
        生产领料预计和实际的对比表查询条件
    """
    _name = 'qdodoo.mrp.actual.theory.wizard'    # 模型名称
    _description = 'qdodoo.mrp.actual.theory.wizard'    # 模型描述

    _columns = {    # 定义字段
        'start_date': fields.date(u'开始日期', required=True),
        'end_date': fields.date(u'结束日期'),
        'analytic_plan': fields.many2one('account.analytic.account',u'辅助核算'),
        'product_id': fields.many2one('product.product',u'产品'),
        'mrp_production': fields.many2one('mrp.production',u'生产单号'),
        'location_id': fields.many2many('stock.location','location_actual_pel','locat_id','actual_id',u'库位')
    }
    def start_date(self,cr,uid,ids,context=None):
        """
            本月初
        """
        now_date = datetime.now()
        day = str(now_date)[:8] + '01 00:00:01'
        return day

    _defaults = {
        'start_date':start_date
        }

    def search_date(self, cr, uid, ids, context=None):
        """
            生产领料预计和实际的对比表
        """
        # 开始时间必须小于等于结束时间
        if context.get('end_date') and context.get('start_date')> context.get('end_date'):
            raise osv.except_osv(_('对不起'),_('开始日期不能大于结束日期！'))
        return {'type' : 'ir.actions.report.xml',
              'report_name': 'qdodoo_mrp_actual_theory_report.report_mrp_actual_theory',
              'report_type' : 'qweb-html',
              'data':context,
              'context' : context,
              'name':u'生产领料预计和实际的对比',
              }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: