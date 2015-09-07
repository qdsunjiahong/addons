#coding:utf-8

from openerp.osv import osv,fields
from openerp import netsvc

class qunar_payment(osv.Model):
    _name="qunar.payment"

    def btn_pay(self,cr,uid,ids,context=None):
        if context==None:
            context={}
        account_invoice_obj = self.pool.get('account.invoice')
        partner_ids=[]
        amount = 0.0
        payment_orders=""
        to_pay_ids=[]
        for id in context.get('active_ids',[]):
            account_invoice = account_invoice_obj.browse(cr,uid,id,context=context)
            to_pay_ids.append(account_invoice.id)
            partner_ids.append(account_invoice.partner_id.id)
            amount += account_invoice.residual
            payment_orders+=account_invoice.name+";"

        if len(list(set(partner_ids)))!=1:
            raise osv.except_osv('Error',"You can't pay more than one supplier at once!'")
        dummy,view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher','view_vendor_receipt_dialog_form')
        print to_pay_ids
        res={
                "name":"Multi Pay",
                "type":"ir.actions.act_window",
                "res_model":"account.voucher",
                "view_mode":"form",
                "view_id":view_id,
                "view_type":"form",
                "target":"new",
                "context":{
                    'payment_expected_currency': account_invoice.currency_id.id,
                    "default_partner_id":partner_ids[0],
                    "default_amount":amount,
                    'close_after_process': True,
                    'invoice_type': account_invoice.type,
                    'invoice_ids': to_pay_ids,
                    "default_reference":payment_orders,
                    'default_type': account_invoice.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'type': account_invoice.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
                    },
                }
                
        return res

class account_voucher(osv.Model):
    _inherit="account.voucher"

    def button_proforma_voucher(self, cr, uid, ids, context=None):
        context = context or {}
        i_ids = context.get('invoice_ids') or []
        wf_service = netsvc.LocalService("workflow")
        for vid in ids:
            voucher = self.pool.get('account.voucher').browse(cr,uid,vid,context=context)
            for line in voucher.line_dr_ids:  
                line_obj = self.pool.get('account.voucher.line').browse(cr,uid,line.id,context=context)  
                if line.move_line_id.invoice.id in i_ids:
                    line_obj.write({'reconcile':True,'amount':line.amount_unreconciled})
                else:
                    line_obj.write({'reconcile':False,'amount':0})
            for line in voucher.line_cr_ids:
                line_obj = self.pool.get('account.voucher.line').browse(cr,uid,line.id,context=context)  
                if line.move_line_id.invoice.id in i_ids:
                    line_obj.write({'reconcile':True,'amount':line.amount_unreconciled})
                else:
                    line_obj.write({'reconcile':False,'amount':0})            
            wf_service.trg_validate(uid, 'account.voucher', vid, 'proforma_voucher', cr)
        return {'type': 'ir.actions.act_window_close'}    