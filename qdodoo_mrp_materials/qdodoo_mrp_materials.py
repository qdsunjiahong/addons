# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models
import time
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class qdodoo_mrp_materials(models.Model):
    """
        生产订单增加强制会计区间字段
    """
    _inherit = 'mrp.production'

    qdodoo_period = fields.Many2one('account.period', u'强制会计区间')

class qdodoo_account_move_tfs(models.Model):
    _inherit = 'account.move'

    move_tfs = fields.Many2one('stock.move',u'转移单',copy=False)

    def create(self, cr, uid, vals, context=None):
        picking_obj = self.pool.get('stock.picking')
        if vals.get('ref'):
            picking_ids = picking_obj.search(cr, uid, [('name','=',vals.get('ref'))])
            if picking_ids:
                acc = picking_obj.browse(cr, uid, picking_ids[0]).acc
                if acc:
                    vals['period_id'] = acc.id
        return super(qdodoo_account_move_tfs, self).create(cr, uid, vals, context=context)

class qdodoo_stock_move_tfs(models.Model):
    _inherit = 'stock.move'

    qdodoo_period = fields.Many2one('account.period', u'强制会计区间')

    def action_done(self, cr, uid, ids, context=None):
        res_id = super(qdodoo_stock_move_tfs, self).action_done(cr, uid, ids, context=context)
        move_obj = self.pool.get('account.move')
        for line_id in self.browse(cr, uid, ids):
            move_ids = move_obj.search(cr, uid, [('move_tfs','=',line_id.id)])
            if line_id.picking_id.acc:
                line_date = line_id.picking_id.acc.date_stop
                period_id = line_id.picking_id.acc.id
            else:
                line_date = line_id.date
                period_id = self.pool.get('account.period').search(cr, uid, [('company_id','=',line_id.company_id.id),('date_start','<=',line_id.date),('date_stop','>=',line_id.date)])[0]
            for move_id in move_ids:
                move_obj.write(cr, uid, move_id, {'date':line_date,'period_id':period_id})
        return res_id

class qdodoo_stock_quant_tfs(models.Model):
    _inherit = 'stock.quant'

    def _create_account_move_line(self, cr, uid, quants, move, credit_account_id, debit_account_id, journal_id,
                                  context=None):
        # group quants by cost
        quant_cost_qty = {}
        for quant in quants:
            if quant_cost_qty.get(quant.cost):
                quant_cost_qty[quant.cost] += quant.qty
            else:
                quant_cost_qty[quant.cost] = quant.qty
        move_obj = self.pool.get('account.move')
        production_obj = move.production_id or move.raw_material_production_id
        for cost, qty in quant_cost_qty.items():
            move_lines = self._prepare_account_move_line(cr, uid, move, qty, cost, credit_account_id, debit_account_id,
                                                         context=context)
            period_id = production_obj.qdodoo_period.id if production_obj and production_obj.qdodoo_period else context.get(
                'force_period', self.pool.get('account.period').find(cr, uid, move.date, context=context)[0])
            move_obj.create(cr, uid, {'journal_id': journal_id,
                                      'line_id': move_lines,
                                      'period_id': period_id or move.period_id.id,
                                      'date': move.date,
                                      'move_tfs': move.id,
                                      'ref': move.picking_id.name}, context=context)
