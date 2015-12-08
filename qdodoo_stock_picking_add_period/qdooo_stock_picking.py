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
        if vals.get('acc', False):
            vals['date_done'] = self.env['account.period'].browse(vals.get('acc')).date_stop
            if self.move_lines:
                for move_line in self.move_lines:
                    move_line.write({'period_id': vals.get('acc')})
        return super(qdodoo_stock_picking_eric, self).write(vals)

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        data = super(qdodoo_stock_picking_eric, self)._get_invoice_vals(cr, uid, key, inv_type, journal_id, move,
                                                                        context=context)
        if move.picking_id.acc:
            data['period_id'] = move.picking_id.acc.id
        return data


