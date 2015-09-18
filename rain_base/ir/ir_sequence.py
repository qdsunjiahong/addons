# -*- coding: utf-8 -*-
import openerp
from openerp.osv import osv, fields
from openerp.tools.translate import _
import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ir_sequence(openerp.osv.osv.osv):
    _inherit = "ir.sequence"
    _columns = {
        'update_date' : openerp.osv.fields.datetime(u'更新时间'),
        'implementation': openerp.osv.fields.selection(
            [('standard', 'Standard'), ('no_gap', 'No gap'),('resetbydate','ResetBydate')],
            'Implementation', required=True),
    }

    _defaults = {
        'update_date': fields.datetime.now
    }

    def _next(self, cr, uid, ids, context=None):
        if not ids:
            return False
        if context is None:
            context = {}
        force_company = context.get('force_company')
        if not force_company:
            force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        sequences = self.read(cr, uid, ids,
                              ['name', 'update_date','company_id', 'implementation', 'number_next', 'prefix', 'suffix', 'padding'])

        preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company]
        seq = preferred_sequences[0] if preferred_sequences else sequences[0]
        if seq['implementation'] == 'standard':
            cr.execute("SELECT nextval('ir_sequence_%03d')" % seq['id'])
            seq['number_next'] = cr.fetchone()
        if seq['implementation'] == 'resetbydate':
            ##修改 添加一个新的实现方法，日期变更后，重新进行计数
            cr.execute("SELECT number_next, update_date FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
            #查看res update_date
            nowdate = datetime.datetime.now()
            res = cr.dictfetchone()
            updte_date_str = res['update_date']
            update_date = datetime.datetime.strptime(updte_date_str, DEFAULT_SERVER_DATETIME_FORMAT)

            if (nowdate-update_date).days != 0:
                nowdate = nowdate.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                cr.execute("UPDATE ir_sequence SET number_next=2, update_date=%s WHERE id=%s ", (nowdate,seq['id']))
                seq['number_next'] = 1
            else:
                cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
            self.invalidate_cache(cr, uid, ['number_next'], [seq['id']], context=context)
        else:
            cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
            cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
            self.invalidate_cache(cr, uid, ['number_next'], [seq['id']], context=context)
        d = self._interpolation_dict()
        try:
            interpolated_prefix = self._interpolate(seq['prefix'], d)
            interpolated_suffix = self._interpolate(seq['suffix'], d)
        except ValueError:
            raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
        return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix