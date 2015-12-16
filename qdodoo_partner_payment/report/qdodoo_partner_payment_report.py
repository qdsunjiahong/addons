# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_partner_payment_report(models.Model):
    """
    供应商账务动态表
    """
    _name = 'qdodoo.partner.payment.report'
    _description = 'qdodoo.partner.payment.report'
    partner_id = fields.Many2one('res.partner', string=u'供应商')
    date = fields.Char(string=u'时间')
    amount = fields.Float(digits=(16, 4), string=u'总金额')
    paid_amount = fields.Float(digits=(16, 4), string=u'已付金额')
    unpaid_amount = fields.Float(digits=(16, 4), string=u'未付金额')
    property_supplier_payment_term = fields.Many2one('account.payment.term', string=u'付款条款')
