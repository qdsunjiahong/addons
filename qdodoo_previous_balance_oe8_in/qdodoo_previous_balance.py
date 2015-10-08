# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api


class qdodoo_previous_balance(models.Model):
    _inherit = 'qdodoo.result.balance.statement'

    @api.depends('current_balance', 'product_id.standard_price')
    def _get_total_mount(self):
        for record in self:
            print record.product_id.standard_price
            record.total_mount = record.product_id.standard_price * record.current_balance

    total_mount = fields.Float(digits=(16, 4), compute='_get_total_mount',string=u'金额')
