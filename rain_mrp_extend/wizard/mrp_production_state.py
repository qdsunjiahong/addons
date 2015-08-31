# -*- coding: utf-8 -*-


from openerp.osv import osv
from openerp.tools.translate import _

class mrp_production_confirm(osv.osv_memory):
    """
    This wizard will confirm the all the selected draft production
    """

    _name = "mrp.production.confirm"

    def production_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        proxy = self.pool['mrp.production']
        for record in proxy.browse(cr, uid, active_ids, context=context):
            if record.state not in ('draft'):
                raise osv.except_osv(_('Warning!'), _("有的记录不是 新建状态 "))
            record.signal_workflow('button_confirm')

        return {'type': 'ir.actions.act_window_close'}
