# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################



from openerp import models, fields


class qdodoo_account_move_line(models.Model):
    _inherit = 'account.move.line'

    location_in_id = fields.Many2one('stock.location', string=u'库位')
    sale_team_id = fields.Many2one('crm.case.section',u'销售团队')

    # 创建分录明细的时候，源单据是否是销售订单，如果是，则获取对应的销售团队
    def create(self, cr, uid, valus, context=None):
        ref = valus.get('ref')
        picking_obj = self.pool.get('stock.picking')
        sale_obj = self.pool.get('sale.order')
        if ref:
            # 获取关联的库存调拨单
            picking_ids = picking_obj.search(cr, uid, [('name','=',ref)])
            if picking_ids:
                for line in picking_obj.browse(cr, uid, picking_ids):
                    # 获取关联的销售订单
                    sale_ids = sale_obj.search(cr, uid, [('name','=',line.origin)])
                    if sale_ids:
                        obj = sale_obj.browse(cr, uid, sale_ids[0])
                        valus['sale_team_id'] = obj.section_id.id if obj.section_id else (obj.partner_id.section_id.id if obj.partner_id.section_id else '')
        return super(qdodoo_account_move_line, self).create(cr, uid, valus, context=context)


class qdodoo_stock_move(models.Model):
    _inherit = 'stock.quant'
    '''
    方法重写
    '''

    def _prepare_account_move_line(self, cr, uid, move, qty, cost, credit_account_id, debit_account_id, context=None):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        if context is None:
            context = {}
        currency_obj = self.pool.get('res.currency')
        if context.get('force_valuation_amount'):
            valuation_amount = context.get('force_valuation_amount')
        else:
            if move.product_id.cost_method == 'average':
                valuation_amount = cost if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal' else move.product_id.standard_price
            else:
                valuation_amount = cost if move.product_id.cost_method == 'real' else move.product_id.standard_price
        valuation_amount = currency_obj.round(cr, uid, move.company_id.currency_id, valuation_amount * qty)
        partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(
            move.picking_id.partner_id).id) or False
        debit_line_vals = {
            'name': move.name,
            'product_id': move.product_id.id,
            'quantity': qty,
            'product_uom_id': move.product_id.uom_id.id,
            'ref': move.picking_id and move.picking_id.name or False,
            'date': move.date,
            'partner_id': partner_id,
            'debit': valuation_amount > 0 and valuation_amount or 0,
            'credit': valuation_amount < 0 and -valuation_amount or 0,
            'account_id': debit_account_id,
            'location_in_id': move.location_dest_id.id,
        }
        credit_line_vals = {
            'name': move.name,
            'product_id': move.product_id.id,
            'quantity': qty,
            'product_uom_id': move.product_id.uom_id.id,
            'ref': move.picking_id and move.picking_id.name or False,
            'date': move.date,
            'partner_id': partner_id,
            'credit': valuation_amount > 0 and valuation_amount or 0,
            'debit': valuation_amount < 0 and -valuation_amount or 0,
            'account_id': credit_account_id,
            'location_in_id': move.location_id.id,
        }
        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
