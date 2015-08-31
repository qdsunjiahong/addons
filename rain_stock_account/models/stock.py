# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _columns = {
        'group_ref':fields.char('Procurement Group Ref',
                            help="",
                            readonly=True, states={'draft': [('readonly', False)]})
    }


class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        if context is None:
            context = {}
        partner, currency_id, company_id, user_id = key
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
            payment_term = partner.property_payment_term.id or False
        else:
            account_id = partner.property_account_payable.id
            payment_term = partner.property_supplier_payment_term.id or False
        return {
            'origin': move.picking_id.name,
            'date_invoice': context.get('date_inv', False),
            'user_id': user_id,
            'partner_id': partner.id,
            'account_id': account_id,
            'payment_term': payment_term,
            'type': inv_type,
            'fiscal_position': partner.property_account_position.id,
            'company_id': company_id,
            'currency_id': currency_id,
            'journal_id': journal_id,
            'group_ref' : move.picking_id.group_id.name
        }