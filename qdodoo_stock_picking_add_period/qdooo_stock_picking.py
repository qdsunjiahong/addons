# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api


class qdodoo_stock_picking_eric(models.Model):
    _inherit = 'stock.picking'

    acc = fields.Many2one('account.period', string=u'强制会计期间')

    @api.multi
    def write(self, vals):
        if vals.get('acc'):
            vals['date_done'] = self.env['account.period'].browse(vals.get('acc')).date_stop
        return super(qdodoo_stock_picking_eric, self).write(vals)
