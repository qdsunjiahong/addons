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

from openerp.osv import osv,orm
from openerp.osv import fields
from openerp import api
from openerp.tools.translate import _
import datetime,time
from openerp.addons.account.account_move_line import account_move_line


class account_move_line_original(osv.osv):
    _inherit = "account.move.line"

    def _invoice(self, cursor, user, ids, name, arg, context=None):
        invoice_obj = self.pool.get('account.invoice')
        res = {}
        for line_id in ids:
            res[line_id] = {'invoice':False,'original':False}
        cursor.execute('SELECT l.id, i.id ' \
                        'FROM account_move_line l, account_invoice i ' \
                        'WHERE l.move_id = i.move_id ' \
                        'AND l.id IN %s',
                        (tuple(ids),))
        invoice_ids = []
        for line_id, invoice_id in cursor.fetchall():
            # 根据对账单编号获取源单据号
            origin = invoice_obj.browse(cursor, user, invoice_id).origin
            res[line_id] = {'invoice':invoice_id,'original':origin}
            invoice_ids.append(invoice_id)
        invoice_names = {False: ''}
        for invoice_id, name in invoice_obj.name_get(cursor, user, invoice_ids, context=context):
            invoice_names[invoice_id] = name
        for line_id in res.keys():
            invoice_id = res[line_id]
            res[line_id] = {'invoice':(invoice_id.get('invoice'), invoice_names[invoice_id.get('invoice')]),'original':invoice_id.get('original')}
        return res

    def get_original2(self, cr, uid, obj, name, args, context=None):
        if not args:
            return []
        account_ids = []
        for line in args:
            account_ids += self.pool.get('account.invoice').search(cr, uid, [('origin',line[1],line[2])])
        return [('invoice','in',account_ids)]


    _columns = {
        'original': fields.function(_invoice, string='源单据',type='char',multi="original", fnct_search=get_original2, store=False, select=True),
        'invoice': fields.function(_invoice, string='Invoice',
            type='many2one', relation='account.invoice', fnct_search=account_move_line._invoice_search,multi="original"),
    }

    def create(self, cr, uid, valu, context=None):
        res_id = super(account_move_line_original, self).create(cr, uid, valu, context=context)
        obj = self.browse(cr, uid, res_id)
        if obj.original:
            super(account_move_line_original, self).write(cr, uid, res_id, {'original2':obj.original})
        return res_id

    def write(self, cr, uid, ids, valu, context=None):
        super(account_move_line_original, self).write(cr, uid, ids, valu, context=context)
        for obj in self.browse(cr, uid, ids):
            if obj.original:
                super(account_move_line_original, self).write(cr, uid, obj.id, {'original2':obj.original})
        return True

