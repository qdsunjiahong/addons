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
