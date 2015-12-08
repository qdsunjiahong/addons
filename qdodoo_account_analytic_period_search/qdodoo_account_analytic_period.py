# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import osv, fields


class qdodoo_account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'
    _columns = {
        "period_id2": fields.many2one('account.period', string=u'会计期间')
    }

    def create(self, cr, uid, vals, context=None):
        print vals.get('date'), vals.get('account_id')
        if vals.get('date', False) and vals.get('account_id', False):
            company_id = self.pool.get("account.analytic.account").browse(cr, uid, vals.get('account_id')).company_id.id
            period_ids = self.pool.get('account.period').search(cr, uid,
                                                                [('date_start', '<=', vals.get('date')),
                                                                 ('date_stop', '>=', vals.get('date')),
                                                                 ('company_id', '=', company_id)])
            vals['period_id2'] = period_ids[0]
        return super(qdodoo_account_analytic_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('date', False):
            company_id = self.browse(cr, uid, ids).company_id.id or \
                         self.pool.get("account.analytic.account").browse(cr, uid, vals.get('account_id')).company_id.id
            period_ids = self.pool.get('account.period').search(cr, uid,
                                                                [('date_start', '<=', vals.get('date')),
                                                                 ('date_stop', '>=', vals.get('date')),
                                                                 ('company_id', '=', company_id)])
            vals['period_id2'] = period_ids[0]
        return super(qdodoo_account_analytic_line, self).write(cr, uid, ids, vals, context=context)
