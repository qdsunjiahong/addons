# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, orm
from openerp.osv import fields
from openerp import api
from openerp.tools.translate import _
import datetime, time
from openerp.addons.account_payment.account_move_line import account_move_line


class account_payment_select(osv.osv):
    _inherit = "payment.order.create"

    def create_payment(self, cr, uid, ids, context=None):
        order_obj = self.pool.get('payment.order')
        line_obj = self.pool.get('account.move.line')
        payment_obj = self.pool.get('payment.line')
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        line_ids = [entry.id for entry in data.entries]
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}
        payment = order_obj.browse(cr, uid, context['active_id'], context=context)
        t = None
        line2bank = line_obj.line2bank(cr, uid, line_ids, t, context)
        ## Finally populate the current payment with new lines:
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if payment.date_prefered == "now":
                # no payment date => immediate payment
                date_to_pay = False
            elif payment.date_prefered == 'due':
                date_to_pay = line.date_maturity
            elif payment.date_prefered == 'fixed':
                date_to_pay = payment.date_scheduled
            # Fix Refunds
            if line.debit:
                line.amount_to_pay = -line.debit
            payment_obj.create(cr, uid, {
                'move_line_id': line.id,
                'amount_currency': line.amount_to_pay,  # line.amount_residual_currency,
                'bank_id': line2bank.get(line.id),
                'order_id': payment.id,
                'partner_id': line.partner_id and line.partner_id.id or False,
                'communication': line.ref or '/',
                'state': line.invoice and line.invoice.reference_type != 'none' and 'structured' or 'normal',
                'date': date_to_pay,
                'currency': (
                                line.invoice and line.invoice.currency_id.id) or line.journal_id.currency.id or line.journal_id.company_id.currency_id.id,
            }, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def search_entries(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('account.move.line')
        payment_obj = self.pool.get('payment.order')
        mod_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        payment_id = payment_obj.browse(cr, uid, context.get('active_id'))
        search_due_date = data.duedate
        domain = [('partner_id', '=', payment_id.payment_supplier.id), ('reconcile_id', '=', False),
                  ('log_is_two', '=', False), ('account_id.type', '=', 'payable'),
                  ('account_id.reconcile', '=', True)]  # ('credit', '>', 0),
        domain = domain + ['|', ('date_maturity', '<=', search_due_date), ('date_maturity', '=', False)]
        line_ids = line_obj.search(cr, uid, domain, context=context)
        context = dict(context, line_ids=line_ids)
        context.update({'line_ids': line_ids})
        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'),
                                                  ('name', '=', 'view_create_payment_order_lines')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {'name': _('Entry Lines'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.order.create',
                'views': [(resource_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                }


class payment_line_inherit(osv.osv):
    _inherit = "payment.line"

    def create(self, cr, uid, vals, context=None):
        line_obj = self.pool.get('account.move.line')
        res_id = super(payment_line_inherit, self).create(cr, uid, vals, context=context)
        if vals.get('move_line_id'):
            line_obj.write(cr, uid, vals.get('move_line_id'), {'log_is_two': True})
        return res_id

    def unlink(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('account.move.line')
        for line in self.browse(cr, uid, ids):
            if line.move_line_id:
                line_obj.write(cr, uid, line.move_line_id.id, {'log_is_two': False})
        return super(payment_line_inherit, self).unlink(cr, uid, ids, context=context)

    def _get_ml_inv_ref(self, cr, uid, ids, *a):
        res = {}
        for id in self.browse(cr, uid, ids):
            res[id.id] = {'ml_inv_ref': False, 'origin': False}
            if id.move_line_id:
                if id.move_line_id.invoice:
                    res[id.id] = {'ml_inv_ref': id.move_line_id.invoice.id, 'origin': id.move_line_id.invoice.origin}
        return res

    _columns = {
        'ml_inv_ref': fields.function(_get_ml_inv_ref, multi='tian', type='many2one', relation='account.invoice',
                                      string='Invoice Ref.'),
        'origin': fields.function(_get_ml_inv_ref, type='char', string='源单据', multi='tian'),
    }


class account_move_line_inherit(osv.osv):
    _inherit = "account.move.line"

    def _amount_residual(self, cr, uid, ids, field_names, args, context=None):
        """ Return the amount still to pay regarding all the payemnt orders
        (excepting cancelled orders)"""
        if not ids:
            return {}
        cr.execute("""SELECT ml.id,
                    CASE WHEN ml.amount_currency < 0
                        THEN - ml.amount_currency
                        ELSE ml.credit
                    END -
                    (SELECT coalesce(sum(amount_currency),0)
                        FROM payment_line pl
                            INNER JOIN payment_order po
                                ON (pl.order_id = po.id)
                        WHERE move_line_id = ml.id
                        AND po.state != 'cancel') AS amount
                    FROM account_move_line ml
                    WHERE id IN %s""", (tuple(ids),))
        r = dict(cr.fetchall())
        return r

    _columns = {
        'log_is_two': fields.boolean(u'是否是第二次选择'),
        # 'amount_to_pay': fields.function(_amount_residual,
        #     type='float', string='Amount to pay', fnct_search=account_move_line._to_pay_search),
    }
    _default = {
        'log_is_two': False,
    }


class account_move_line_inherit(osv.osv):
    _inherit = "payment.order"

    def fields_get(self, cr, uid, fields=None, context=None, write_access=True, attributes=None):
        res = super(account_move_line_inherit, self).fields_get(cr, uid, fields, context, write_access, attributes)
        if 'communication2' in res:
            res['communication2'].setdefault('states', {})
            res['communication2']['states']['structured'] = [('readonly', True)]
            res['communication2']['states']['normal'] = [('readonly', False)]
        return res

    def unlink(self, cr, uid, ids, context=None):
        """
            只能删除草稿状态的付款单，并且删除付款单后将对应的分录明细的标志是否已被选择的字段置为false
        """
        account_obj = self.pool.get('account.move.line')
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state == 'done':
                raise osv.except_osv(_(u'提醒'), _(u'不能删除完成状态的付款单'))
            for line_id in rec.line_ids:
                if line_id.move_line_id:
                    account_obj.write(cr, uid, line_id.move_line_id.id, {'log_is_two': False})
        return super(account_move_line_inherit, self).unlink(cr, uid, ids, context=context)

    def _get_location_name(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for order_obj in self.browse(cr, uid, ids, context=None):
            if order_obj.line_ids:
                origin = order_obj.line_ids[0].origin
                if origin:
                    if "/" in origin:
                        origin_list = origin.split("/")
                        res[order_obj.id] = origin_list[0]
                    elif "\\" in origin:
                        origin_list = origin.split("\\")
                        res[order_obj.id] = origin_list[0]
                    else:
                        po_obj = self.pool.get('purchase.order')
                        po_ids = po_obj.search(cr, uid, [('name', '=', origin)])
                        if po_ids:
                            res[order_obj.id] = po_obj.browse(cr, uid, po_ids[0]).location_id.name
                        else:
                            res[order_obj.id] = u'暂无明细'
                else:
                    res[order_obj.id] = u'暂无明细'
            else:
                res[order_obj.id] = u'暂无明细'
        return res

    _columns = {
        "location_name": fields.function(_get_location_name, type="char", string=u'库位')
    }
