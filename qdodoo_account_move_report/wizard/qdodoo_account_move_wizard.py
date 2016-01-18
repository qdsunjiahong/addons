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

    # @api.multi
    def report_print(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('account.move')
        report_obj = self.pool.get('qdodoo.account.move.report')
        # 删除需打印数据表中数据
        report_ids = report_obj.search(cr, uid, [])
        report_obj.unlink(cr, uid, report_ids)
        # 创建需打印数据（循环所有选中的凭证数据）
        id_list = []
        for move_id in move_obj.browse(cr, uid, context.get('active_ids')):
            # 循环凭证明细
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
                # 创建需打印的数据
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
