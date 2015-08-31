# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from openerp import fields,models,api,_ 

class qunar_balance_ledger_filter_partner(models.Model):
	_inherit="account.partner.ledger"

	partner_id = fields.Many2one('res.partner','Partner')

	@api.multi
	def _print_report(self,data):
		data = self.pre_print_report(data)
		data['form'].update(self.read(['initial_balance', 'filter', 'page_split', 'amount_currency'])[0])
		data['form'].update({'partner_id':self.partner_id.id or False})
		if data['form'].get('page_split') is True: 
			return self.env['report'].get_action(self,'account.report_partnerledgerother',data)
		return self.env['report'].get_action(self,'account.report_partnerledger',data)

from openerp.addons.account.report import account_partner_ledger 

class qunar_partner_bedger(account_partner_ledger.third_party_ledger):

 	def set_context(self, objects, data, ids, report_type=None):
		obj_move = self.pool.get('account.move.line')
		obj_partner = self.pool.get('res.partner')
		self.query = obj_move._query_get(self.cr, self.uid, obj='l', context=data['form'].get('used_context', {}))
		ctx2 = data['form'].get('used_context',{}).copy()
		self.initial_balance = data['form'].get('initial_balance', True)
		if self.initial_balance:
		    ctx2.update({'initial_bal': True})
		self.init_query = obj_move._query_get(self.cr, self.uid, obj='l', context=ctx2)
		self.reconcil = True
		if data['form']['filter'] == 'unreconciled':
		    self.reconcil = False
		self.result_selection = data['form'].get('result_selection', 'customer')
		if data['form'].get('amount_currency'):
		    self.amount_currency['currency'] = True
		else:
		    self.amount_currency.pop('currency', False)
		self.target_move = data['form'].get('target_move', 'all')
		PARTNER_REQUEST = ''
		move_state = ['draft','posted']
		if self.target_move == 'posted':
		    move_state = ['posted']
		if self.result_selection == 'supplier':
		    self.ACCOUNT_TYPE = ['payable']
		elif self.result_selection == 'customer':
		    self.ACCOUNT_TYPE = ['receivable']
		else:
		    self.ACCOUNT_TYPE = ['payable','receivable']

		self.cr.execute(
		    "SELECT a.id " \
		    "FROM account_account a " \
		    "LEFT JOIN account_account_type t " \
		        "ON (a.type=t.code) " \
		        'WHERE a.type IN %s' \
		        "AND a.active", (tuple(self.ACCOUNT_TYPE), ))
		self.account_ids = [a for (a,) in self.cr.fetchall()]
		params = [tuple(move_state), tuple(self.account_ids)]
		#if we print from the partners, add a clause on active_ids
		if (data['model'] == 'res.partner') and ids:
		    PARTNER_REQUEST =  "AND l.partner_id IN %s"
		    params += [tuple(ids)]
		reconcile = "" if self.reconcil else "AND l.reconcile_id IS NULL "
		self.cr.execute(
		        "SELECT DISTINCT l.partner_id " \
		        "FROM account_move_line AS l, account_account AS account, " \
		        " account_move AS am " \
		        "WHERE l.partner_id IS NOT NULL " \
		            "AND l.account_id = account.id " \
		            "AND am.id = l.move_id " \
		            "AND am.state IN %s"
		            "AND " + self.query +" " \
		            "AND l.account_id IN %s " \
		            " " + PARTNER_REQUEST + " " \
		            "AND account.active " + reconcile + " ", params)
		self.partner_ids = [res['partner_id'] for res in self.cr.dictfetchall()]
		#[Note] Add to filter the partner according to your selected partner.
		if data['form'].get('partner_id',False):
			self.partner_ids = data['form']['partner_id']
		print '**********'
		print data
		objects = obj_partner.browse(self.cr, SUPERUSER_ID, self.partner_ids)
		objects = sorted(objects, key=lambda x: (x.ref, x.name))
		return super(third_party_ledger, self).set_context(objects, data, self.partner_ids, report_type)