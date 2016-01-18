# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_account_move_wizard(models.Model):
    _name = 'qdodoo.account.move.wizard'
    _description = 'qdodoo.account.move.wizard'

    def _get_move_lines(self):
        move_lines = ""
        context = self._context or {}
        if context.get('active_model', False) == 'account.move':
            action_ids = context.get('active_ids', [])
            for action_id in action_ids:
                move_lines += str(action_id) + ";"
            return move_lines[0:-1]

    move_line_ids = fields.Char(string=u'会计凭证', default=_get_move_lines)

    # @api.multi
    def report_print(self, cr, uid, ids, context=None):
        context = context or {}
        move_line_ids = self.browse(cr, uid, ids[0]).move_line_ids.split(";")
        move_ids = []
        for move_line_id in move_line_ids:
            move_ids.append(int(move_line_id))
        move_obj = self.pool.get('account.move')
        report_obj = self.pool.get('qdodoo.account.move.report')
        report_ids = report_obj.search(cr, uid, [])
        report_obj.unlink(cr, uid, report_ids)
        id_list = []
        for move_id in move_obj.browse(cr, uid, move_ids):
            for line_id in move_id.line_id:
                data = {
                    'invoice': line_id.invoice.name,
                    'name': line_id.name,
                    'product_name': line_id.product_id.name,
                    'partner_name': line_id.partner_id.name,
                    'debit': line_id.debit,
                    'credit': line_id.credit,
                    'account_analytic': line_id.analytic_account_id.name,
                    'account_name': line_id.account_id.code + '-' + line_id.account_id.name
                }
                create_id = report_obj.create(cr, uid, data)
                id_list.append(create_id)
        context['active_ids'] = id_list
        context['active_model'] = 'qdodoo.account.move.report'
        return self.pool.get("report").get_action(cr, uid, [], 'qdodoo_account_move_report.qdodoo_account_move_report2',
                                                  context=context)


class qdodoo_account_move_report(models.Model):
    _name = 'qdodoo.account.move.report'
    _description = 'qdodoo.account.move.report'

    invoice = fields.Char(string=u'开发票')
    name = fields.Char(string=u'名称')
    product_name = fields.Char(string=u'产品')
    partner_name = fields.Char(string=u'业务伙伴')
    debit = fields.Float(string=u'借方')
    credit = fields.Float(string=u'贷方')
    account_analytic = fields.Char(string=u'辅助核算项')
    account_name = fields.Char(string=u'科目')
