# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class qdodoo_account_print(models.Model):
    """
        批量整合打印POS财务数据
    """

    _name = 'qdodoo.account.print'

    all_num = fields.Float(u'总金额', compute='_get_all_money')
    order_line = fields.One2many('qdodoo.account.print.line','order_id',u'明细')

    def _get_all_money(self):
        for ids in self:
            ids.all_num = 0.0
            for line in ids.order_line:
                ids.all_num += line.money

    @api.multi
    def btn_print(self):
        session_obj = self.env['pos.session']
        session_ids = session_obj.browse(self._context.get('active_ids'))
        account_info = {}
        for session_id in session_ids:
            if session_id.state != 'closed':
                raise osv.except_osv(_(u'警告'),_(u'只能打印处于关闭状态的会话记录！'))
            for line in session_id.statement_ids:
                if line.journal_id in account_info:
                    account_info[line.journal_id] += line.balance_end
                else:
                    account_info[line.journal_id] = line.balance_end
        ids = self.search([])
        ids.unlink()
        order_line = []
        for key,value in account_info.items():
            order_line.append((0,0,{'name':key.id,'money':value}))
        res_id = self.create({'order_line':order_line})
        context = dict(self._context or {}, active_ids=res_id.ids)
        return self.pool["report"].get_action(self._cr, self._uid, res_id.id, 'wxsite.report_account_print', context=context)

class qdodoo_account_print_line(models.Model):
    """
        批量整合打印POS财务数据
    """

    _name = 'qdodoo.account.print.line'

    order_id = fields.Many2one('qdodoo.account.print',u'结账单')
    name = fields.Many2one('account.journal',u'结账方式')
    money = fields.Float(u'金额')