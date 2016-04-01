# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from datetime import datetime
from openerp.exceptions import except_orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.tools.float_utils import float_compare


class stock_picking(models.Model):
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
        if payment_term:
            pterm = self.pool.get('account.payment.term').browse(cr, uid, payment_term)
            pterm_list = pterm.compute(value=1, date_ref=context.get('date_inv', []))
            if pterm_list:
                date_due = max(line[0] for line in pterm_list[0])
            else:
                date_due = False
            return {
                'origin': move.picking_id.name,
                'date_invoice': context.get('date_inv', False),
                'date_due': date_due,
                'user_id': user_id,
                'partner_id': partner.id,
                'account_id': account_id,
                'payment_term': payment_term,
                'type': inv_type,
                'fiscal_position': partner.property_account_position.id,
                'company_id': company_id,
                'currency_id': currency_id,
                'journal_id': journal_id,
                'group_ref': move.picking_id.group_id.name
            }
        else:
            return {
                'origin': move.picking_id.name,
                'date_invoice': context.get('date_inv', False),
                'date_due': False,
                'user_id': user_id,
                'partner_id': partner.id,
                'account_id': account_id,
                'payment_term': payment_term,
                'type': inv_type,
                'fiscal_position': partner.property_account_position.id,
                'company_id': company_id,
                'currency_id': currency_id,
                'journal_id': journal_id,
                'group_ref': move.picking_id.group_id.name
            }
