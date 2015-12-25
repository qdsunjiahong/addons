# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models
from openerp.osv import osv
import time
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_supplier_attachment_search(models.Model):
    """
        供应商证件查询表
    """
    _name = 'qdodoo.supplier.attachment.search'    # 模型名称
    _description = 'qdodoo.supplier.attachment.search'    # 模型描述

    partner_id = fields.Many2many('res.partner','supplier_attachment_search','search_id','partner_id',u'供应商')
    date_start = fields.Date(u'开始时间')
    date_end = fields.Date(u'结束时间')

    def search_date(self, cr, uid, ids, context=None):
        sql_1 = """delete from qdodoo_supplier_attachment_report where 1=1"""
        cr.execute(sql_1)
        res_id = []
        if context.get('date_end') < context.get('date_start'):
            raise osv.except_osv(_('错误'),_('开始日期不能大于结束日期！'))
        attachment_obj = self.pool.get('ir.attachment')
        supplier_obj = self.pool.get('qdodoo.supplier.attachment.report')
        domain = [('create_date','>=',context.get('date_start')),('create_date','<=',context.get('date_end')),('res_model','=',False)]
        if context.get('partner_id')[0][2]:
            domain += [('partner_id','in',context.get('partner_id')[0][2])]
        else:
            domain += [('partner_id','!=',False)]
        attachment_ids = attachment_obj.search(cr, uid, domain)
        for line in attachment_obj.browse(cr, uid, attachment_ids):
            if datetime.now().date().strftime('%Y-%m-%d') > line.attachment_endtime:
                overdue = 'yes'
            else:
                overdue = 'no'
            res = supplier_obj.create(cr, uid, {'partner_id':line.partner_id.id,
                                                'name':line.id,'num':1,
                                                'date_start':line.attachment_starttime,
                                                'date_end':line.attachment_endtime,
                                                'overdue':overdue,
                                                'user_id':line.user_id.id})
            res_id.append(res)
        mod_obj = self.pool.get('ir.model.data')
        view_mode, view_id = mod_obj.get_object_reference(cr, uid, 'qdodoo_supplier_attachment_report', 'view_tree_qdodoo_supplier_attachment_report')
        view_search_mode, view_search_id = mod_obj.get_object_reference(cr, uid, 'qdodoo_supplier_attachment_report', 'view_search_qdodoo_supplier_attachment_report')
        return {
            'name': _('供应商证件'),
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'qdodoo.supplier.attachment.report',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', res_id)],
            'views': [(view_id, 'tree')],
            'view_id': [view_id],
            'search_view_id': [view_search_id],
        }
