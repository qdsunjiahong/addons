# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp import osv

class qdodoo_partner_banks(models.Model):
    """
        在银行账户信息中增加供应商信息
    """
    _inherit = 'res.partner.bank'

    ref = fields.Char(u'内部编吗',related='partner_id.ref')
    phone = fields.Char(u'电话',related='partner_id.phone')
    email = fields.Char(u'Email', related='partner_id.email')
    payment_term = fields.Char(u'付款条款', related='partner_id.property_supplier_payment_term.name')
    credit = fields.Float(u'应收款合计', related='partner_id.credit')
    debit = fields.Float(u'应付款合计', related='partner_id.debit')
