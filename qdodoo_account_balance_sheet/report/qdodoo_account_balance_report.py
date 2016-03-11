# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:qdodoo suifeng
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields, _, api
from openerp import tools
import openerp.addons.decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


class qdodoo_account_balance(models.TransientModel):
    """
    科目余额表
    """
    _name = "qdodoo.account.balance"
    _rec_name = 'account_id'

    period_id = fields.Many2one('account.period', string=u'期间', readonly=True)
    account_id = fields.Many2one('account.account', string=u'科目', readonly=True)
    debit = fields.Float(string=u'借方', readonly=True)
    credit = fields.Float(string=u'贷方', readonly=True)
    starting_balance = fields.Float(string=u'期初余额', readonly=True)
    ending_balance = fields.Float(string=u'期末余额', readonly=True)
    company_id = fields.Many2one('res.company', string=u'公司', readonly=True)
    partner_ids = fields.One2many('qdodoo.account.balance.partner', 'account_periodly_id', string=u'明细')


class qdodoo_account_balance_partner(models.TransientModel):
    _name = 'qdodoo.account.balance.partner'
    _description = 'qdodoo.account.balance.partner'
    _rec_name = 'partner_id'

    account_periodly_id = fields.Many2one('qdodoo.account.balance', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string=u'业务伙伴', readonly=True)
    period_id = fields.Many2one('account.period', string=u'期间', readonly=True)
    company_id = fields.Many2one('res.company', string=u'公司', readonly=True)
    start_balance = fields.Float(string=u'期初', readonly=True)
    debit = fields.Float(string=u'借方', readonly=True)
    credit = fields.Float(string=u'贷方', readonly=True)
    end_balance = fields.Float(string=u'期末', readonly=True)
    account_id = fields.Many2one('account.account', string=u'科目', readonly=True)
    line_ids = fields.One2many('qdodoo.balance.partner.line', 'report_id', string=u'明细')


class qdodoo_account_partner_line(models.TransientModel):
    _name = 'qdodoo.balance.partner.line'
    _description = 'qdodoo.balance.partner.line'

    report_id = fields.Many2one('qdodoo.account.balance.partner', string=u'业务伙伴', readonly=True, ondelete='cascade')
    period_id = fields.Many2one('account.period', string=u'期间', readonly=True)
    company_id = fields.Many2one('res.company', string=u'公司', readonly=True)
    debit = fields.Float(string=u'借方', readonly=True)
    credit = fields.Float(string=u'贷方', readonly=True)
    account_id = fields.Many2one('account.account', string=u'科目', readonly=True)
    move_name = fields.Many2one('account.move',string=u'凭证号', readonly=True)
    line_name = fields.Many2one('account.move.line',string=u'名称', readonly=True)
