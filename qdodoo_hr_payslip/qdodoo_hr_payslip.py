###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields
from datetime import datetime
from dateutil import relativedelta


class qdodoo_hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    def _default_get_date_from(self, cr, uid, context=None):
        date_now = str(datetime.now() + relativedelta.relativedelta())
        account_period = date_now[5:7] + "/" + date_now[0:4]
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
        period_obj = self.pool.get("account.period")
        period_ids = period_obj.search(cr, uid, [('company_id', '=', company_id), ('name', '=', account_period)])
        period_brw = period_obj.browse(cr, uid, period_ids[0], context=context)
        return period_brw.date_start

    def _default_get_date_to(self, cr, uid, context=None):
        date_now = str(datetime.now() + relativedelta.relativedelta())
        account_period = date_now[5:7] + "/" + date_now[0:4]
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
        period_obj = self.pool.get("account.period")
        period_ids = period_obj.search(cr, uid, [('company_id', '=', company_id), ('name', '=', account_period)])
        period_brw = period_obj.browse(cr, uid, period_ids[0], context=context)
        return period_brw.date_stop

    _defaults = {
        'date_from': _default_get_date_from,
        'date_to': _default_get_date_to
    }
