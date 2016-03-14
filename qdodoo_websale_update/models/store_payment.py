# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.osv import osv
from datetime import datetime

class qdodoo_account_voucher_inherit(models.Model):
    _inherit = 'account.voucher'

    store_id = fields.Many2one('store.deposit',u'存款单')

    def unlink(self, cr, uid, ids, context=None):
        store_obj = self.pool.get('store.deposit')
        for obj in self.browse(cr, uid, ids):
            if obj.store_id and obj.store_id.state == 'done':
                store_obj.write(cr, uid, obj.store_id.id, {'state':'sent'})
        return super(qdodoo_account_voucher_inherit, self).unlink(cr, uid, ids, context=context)

    def cancel_voucher(self, cr, uid, ids, context=None):
        store_obj = self.pool.get('store.deposit')
        for obj in self.browse(cr, uid, ids):
            if obj.store_id and obj.store_id.state == 'done':
                store_obj.write(cr, uid, obj.store_id.id, {'state':'sent'})
        return super(qdodoo_account_voucher_inherit, self).cancel_voucher(cr, uid, ids, context=context)

class store_deposit(models.Model):
    _name = "store.deposit"
    _order = 'id desc'

    name = fields.Many2one('res.partner',string='账户',required=True)
    voucher_id = fields.Many2one('account.voucher',string='付款单')
    deposit_time = fields.Datetime(string='存款时间', required=True)
    locat_deposit = fields.Char('地点', required=True)
    money = fields.Float(string='金额', digits=(20, 2), required=True)
    remarks = fields.Text(string='备注')
    company_id = fields.Many2one(related='name.company_id', relation='res.company',string='备注')
    state = fields.Selection([('draft',u'草稿'),('sent',u'待审核'),('done',u'待记账'),('over',u'完成'),('cancel',u'取消')],u'状态')

    def _get_user(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users')
        return user.browse(cr, uid, uid).partner_id.id

    # 提交申请
    def btn_sent(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.money <= 0:
            raise osv.except_osv(_(u'警告!'), _(u'存入金额必须大于0!'))
        return self.write(cr, uid, ids, {'state':'sent'})

    # 审批通过
    def btn_done(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal')
        journal_id = journal_obj.search(cr, 1, [('company_id','=',obj.name.company_id.id),('type','=','bank')])
        val = {}
        val['partner_id'] = obj.name.id
        val['amount'] = obj.money
        val['company_id'] = obj.name.company_id.id
        val['type'] = 'receipt'
        val['pre_line'] = True
        val['store_id'] = ids[0]
        if journal_id:
            val['joutnal_id'] = journal_id[0]
            journal = journal_obj.browse(cr, uid, journal_id[0])
            if journal.type in ('sale','sale_refund'):
                val['account_id'] = obj.name.property_account_receivable.id
            elif journal.type in ('purchase', 'purchase_refund','expense'):
                val['account_id'] = obj.name.property_account_payable.id
            else:
                if not journal.default_credit_account_id or not journal.default_debit_account_id:
                    raise osv.except_osv(_('Error!'), _('Please define default credit/debit accounts on the journal "%s".') % (journal.name))
                val['account_id'] = journal.default_credit_account_id.id or journal.default_debit_account_id.id
        else:
            raise osv.except_osv(_(u'警告!'), _(u'缺少对应的账簿!'))
        voucher_id = voucher_obj.create(cr, uid, val)
        return self.write(cr, uid, ids, {'state':'done','voucher_id':voucher_id})

    # 申请驳回
    def btn_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'draft'})

    # 付款
    def btn_over(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        voucher_obj = self.pool.get('account.voucher')
        checking_obj = self.pool.get('qdodoo.checking.list')
        voucher_obj.proforma_voucher(cr, uid, [obj.voucher_id.id])
        if obj.name.credit < 0:
            all_money = -obj.name.credit
        else:
            all_money = 0.0
        checking_obj.create(cr, uid, {'user_id':obj.name.id,'date':datetime.now(),'recharge':obj.money,'type':'beforehand','notes':obj.voucher_id.name,'all_money':all_money})
        return self.write(cr, uid, ids, {'state':'over'})

    # 取消
    def btn_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'cancel'})

    _defaults = {
        'name': _get_user,
        'state': 'draft',
    }

