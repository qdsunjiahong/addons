# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_stock_move(models.Model):
    _inherit = 'stock.move'

    def _get_period_id(self):
        date = fields.Date.today()
        company_id = self.env['res.users'].browse(self.env.uid).company_id.id
        period_ids = self.env['account.period'].search(
            [('company_id', '=', company_id), ('date_start', '<=', date), ('date_stop', '>=', date)])
        return period_ids[0].id

    period_id = fields.Many2one('account.period', copy=False, default=_get_period_id)
