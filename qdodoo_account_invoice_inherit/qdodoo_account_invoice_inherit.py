# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models,fields
from openerp.osv import osv
import time
from datetime import timedelta, datetime



class qdodoo_account_invoice_inherit(models.Model):
    """
        在发票的源单据中增加上采购单号或销售单号
    """
    _inherit = 'account.invoice'    # 继承

    payment_state = fields.Char(u'付款申请状态',compute="_get_payment_state")

    def _get_payment_state(self):
        payment_line_obj = self.env['payment.line']
        for ids in self:
            if ids.move_id and ids.move_id.line_id:
                inv_mv_lines = [x.id for x in ids.move_id.line_id]
                pl_line_ids = payment_line_obj.search([('move_line_id','in',inv_mv_lines)])
                if pl_line_ids:
                    ids.payment_state = u'已申请'
                else:
                    ids.payment_state = u'未申请'
            else:
                ids.payment_state = u'未申请'

    def create(self, cr, uid, vals, context=None):
        if vals.get('origin', '') and vals.get('group_ref'):
            vals['origin'] = vals.get('origin', '') + ':' + vals.get('group_ref')
        return super(qdodoo_account_invoice_inherit, self).create(cr, uid, vals, context=context)

class qdodoo_read_account_move_line(osv.osv_memory):

    """
        在分录明细中增加查询目的库位按钮按钮
    """
    _name = 'qdodoo.read.account.move.line'    # 继承

    def btn_merge(self, cr, uid, ids, context=None):
        lst_ids = []
        line_ids = context.get('active_ids')
        line_obj = self.pool.get('account.move.line')
        for line_id in line_obj.browse(cr, uid, line_ids):
            for line in line_id.move_id.line_id:
                if line.id != line_id.id:
                    lst_ids.append(line.id)
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_line_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_line_form')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': '账务分录',
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'account.move.line',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',lst_ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }







