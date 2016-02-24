# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################



from openerp import models, fields, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class qdodoo_account_move_line(models.Model):
    _inherit = 'account.move.line'

    location_in_id = fields.Many2one('stock.location', string=u'库位')
    sale_team_id = fields.Many2one('crm.case.section',u'销售团队')

    # 创建分录明细的时候，源单据是否是销售订单，如果是，则获取对应的销售团队
    def create(self, cr, uid, valus, context=None):
        ref = valus.get('ref')
        picking_obj = self.pool.get('stock.picking')
        sale_obj = self.pool.get('sale.order')
        account_obj = self.pool.get('account.account')
        # 判断辅助核算项是否正确
        if valus.get('account_id'):
            # 判断科目中的辅助核算项是否必填
            required_assistant = account_obj.browse(cr, uid, valus.get('account_id')).required_assistant
            if required_assistant:
                if not valus.get('analytic_account_id'):
                    raise except_orm(_(u'警告'), _(u'辅助核算项必填！'))
            else:
                if valus.get('analytic_account_id'):
                    valus.pop('analytic_account_id')
                    # raise except_orm(_(u'警告'), _(u'此科目不能录入辅助核算项！'))
        if ref:
            # 获取关联的库存调拨单
            picking_ids = picking_obj.search(cr, uid, [('name','=',ref)])
            if picking_ids:
                for line in picking_obj.browse(cr, uid, picking_ids):
                    # 获取关联的销售订单
                    sale_ids = sale_obj.search(cr, uid, [('name','=',line.origin)])
                    if sale_ids:
                        obj = sale_obj.browse(cr, uid, sale_ids[0])
                        valus['sale_team_id'] = obj.section_id.id if obj.section_id else (obj.user_id.default_section_id.id if obj.user_id.default_section_id else '')
        return super(qdodoo_account_move_line, self).create(cr, uid, valus, context=context)

    def write(self, cr, uid, ids, vals, context=None, check=True):
        res = super(qdodoo_account_move_line, self).write(cr, uid, ids, vals, context=context, check=True)
        for obj in self.browse(cr, uid, ids):
            required_assistant = obj.account_id.required_assistant
            analytic_account_id = obj.analytic_account_id
            if required_assistant:
                if not analytic_account_id:
                    raise except_orm(_(u'警告'), _(u'辅助核算项必填！'))
            else:
                if analytic_account_id:
                    raise except_orm(_(u'警告'), _(u'此科目不能录入辅助核算项！'))
        return res

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
                valuation_amount = cost if ((move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal') or (move.location_id.usage == 'internal' and move.location_dest_id.usage == 'supplier')) else move.product_id.standard_price
            else:
                valuation_amount = cost if move.product_id.cost_method == 'real' else move.product_id.standard_price
        valuation_amount = currency_obj.round(cr, uid, move.company_id.currency_id, valuation_amount * qty)
        partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(
            move.picking_id.partner_id).id) or False
        # 判断如果是生产库存盘点，则增加对应的辅助核算项
        analytic_account_id = ''
        if move.inventory_id:
            analytic_account_id = move.inventory_id.account_assistant.id
        debit_line_vals = {
            'analytic_account_id': analytic_account_id,
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
            'analytic_account_id': analytic_account_id,
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
