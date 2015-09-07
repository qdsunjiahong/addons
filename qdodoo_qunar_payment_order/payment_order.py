# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import osv, fields
from openerp import netsvc


class qunar_payment(osv.Model):
    _name = "qunar.payment"

    def btn_pay(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        account_invoice_obj = self.pool.get('account.invoice')
        partner_ids = []
        amount = 0.0
        payment_orders = ""
        to_pay_ids = []
        for id in context.get('active_ids', []):
            account_invoice = account_invoice_obj.browse(cr, uid, id, context=context)
            to_pay_ids.append(account_invoice.id)
            partner_ids.append(account_invoice.partner_id.id)
            amount += account_invoice.residual
            if account_invoice.name:
                payment_orders += account_invoice.name + ";"

        if len(list(set(partner_ids))) != 1:
            raise osv.except_osv('Error', "You can't pay more than one supplier at once!'")
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher',
                                                                             'view_vendor_receipt_dialog_form')
        res = {
            "name": "Multi Pay",
            "type": "ir.actions.act_window",
            "res_model": "account.voucher",
            "view_mode": "form",
            "view_id": view_id,
            "view_type": "form",
            "target": "new",
            "context": {
                'payment_expected_currency': account_invoice.currency_id.id,
                "default_partner_id": partner_ids[0],
                "default_amount": amount,
                'close_after_process': True,
                'invoice_type': account_invoice.type,
                'invoice_ids': to_pay_ids,
                "default_reference": payment_orders,
                'default_type': account_invoice.type in ('out_invoice', 'out_refund') and 'receipt' or 'payment',
                'type': account_invoice.type in ('out_invoice', 'out_refund') and 'receipt' or 'payment'
            },
        }

        return res


class qdodoo_account_voucher_inherit(osv.Model):
    _inherit = "account.voucher"

    def button_proforma_voucher(self, cr, uid, ids, context=None):
        context = context or {}
        i_ids = context.get('invoice_ids') or []
        wf_service = netsvc.LocalService("workflow")
        for vid in ids:
            voucher = self.pool.get('account.voucher').browse(cr, uid, vid, context=context)
            for line in voucher.line_dr_ids:
                line_obj = self.pool.get('account.voucher.line').browse(cr, uid, line.id, context=context)
                if line.move_line_id.invoice.id in i_ids:
                    line_obj.write({'reconcile': True, 'amount': line.amount_unreconciled})
                else:
                    line_obj.write({'reconcile': False, 'amount': 0})
            for line in voucher.line_cr_ids:
                line_obj = self.pool.get('account.voucher.line').browse(cr, uid, line.id, context=context)
                if line.move_line_id.invoice.id in i_ids:
                    line_obj.write({'reconcile': True, 'amount': line.amount_unreconciled})
                else:
                    line_obj.write({'reconcile': False, 'amount': 0})
            wf_service.trg_validate(uid, 'account.voucher', vid, 'proforma_voucher', cr)
        return {'type': 'ir.actions.act_window_close'}

class payment_order_inherit(osv.Model):
    _inherit = "payment.order"

    def btn_select_order(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        move_lst = []
        for line in obj.line_ids:
            if line.move_line_id.invoice.id not in move_lst:
                move_lst.append(line.move_line_id.invoice.id)
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_tree')
        view_id = result and result[1] or False
        return {
              'name': ('发票'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'account.invoice',
              'type': 'ir.actions.act_window',
              'domain': [('id','in',move_lst)],
              'views': [(view_id,'tree'),(False,'form')],
              'view_id': [view_id],
              }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: