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

    @api.model
    def create(self, vals):
        res = super(qdodoo_stock_move, self).create(vals)
        if res.create_date and res.company_id:
            period_ids = self.env['account.period'].search(
                [('company_id', '=', res.company_id.id), ('date_start', '<=', res.create_date[:10]),
                 ('date_stop', '>=', res.create_date[:10])])
            res.write({'period_id': period_ids[0].id})
        return res

    period_id = fields.Many2one('account.period', string=u'会计期间', copy=False)
