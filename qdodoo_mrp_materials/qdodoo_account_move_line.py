# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################



from openerp import models, fields


class qdodoo_stock_quant_inherit(models.Model):
    _inherit = 'stock.quant'
    '''
    方法重写
    '''

    def _prepare_account_move_line(self, cr, uid, move, qty, cost, credit_account_id, debit_account_id, context=None):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        location_model_us, location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock',
                                                                                             'location_production')
        if context is None:
            context = {}
        print context,8888888
        if context.get('active_model') == 'mrp.production':
            if move.location_dest_id.id == location_id:
                produce_ids = self.pool.get("mrp.production").search(cr, uid, [('name', '=', move.name)])
                mrp_obj = self.pool.get("mrp.production").browse(cr, uid, produce_ids[0])
                currency_obj = self.pool.get('res.currency')
                if context.get('force_valuation_amount'):
                    valuation_amount = context.get('force_valuation_amount')
                else:
                    if move.product_id.cost_method == 'average':
                        valuation_amount = cost if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal' else move.product_id.standard_price
                    else:
                        valuation_amount = cost if move.product_id.cost_method == 'real' else move.product_id.standard_price
                # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
                # the company currency... so we need to use round() before creating the accounting entries.
                valuation_amount = currency_obj.round(cr, uid, move.company_id.currency_id, valuation_amount * qty)
                partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(
                    move.picking_id.partner_id).id) or False
                debit_line_vals = {
                    'name': move.name,
                    'product_id': mrp_obj.product_id.id,
                    'quantity': qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': move.date,
                    'partner_id': partner_id,
                    'debit': valuation_amount > 0 and valuation_amount or 0,
                    'credit': valuation_amount < 0 and -valuation_amount or 0,
                    'account_id': debit_account_id,
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
                }
                return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]

            else:
                bom_cost_list = []
                bom_cost_price = 0
                produce_ids = self.pool.get("mrp.production").search(cr, uid, [('name', '=', move.name)])
                mrp_obj = self.pool.get("mrp.production").browse(cr, uid, produce_ids[0])
                currency_obj = self.pool.get('res.currency')
                if context.get('force_valuation_amount'):
                    valuation_amount = context.get('force_valuation_amount')
                else:
                    if move.product_id.cost_method == 'average':
                        valuation_amount = cost if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal' else move.product_id.standard_price
                    else:
                        valuation_amount = cost if move.product_id.cost_method == 'real' else move.product_id.standard_price
                # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
                # the company currency... so we need to use round() before creating the accounting entries.
                valuation_amount = currency_obj.round(cr, uid, move.company_id.currency_id, valuation_amount * qty)
                partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(
                    move.picking_id.partner_id).id) or False
                for line in mrp_obj.bom_id.bom_cost_ids:
                    cost_debit_vals = {
                        'name': move.name,
                        'product_id': line.name.id,
                        'quantity': line.num,
                        'product_uom_id': line.name.uom_id.id,
                        'date': move.date,
                        'partner_id': partner_id,
                        'debit': line.num * line.unit_price,
                        'credit': 0.0,
                        'account_id': line.name.categ_id.property_stock_account_input_categ.id,
                    }
                    bom_cost_list.append((0, 0, cost_debit_vals))
                    bom_cost_price += line.num * line.unit_price
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
                }
                bom_cost_list.append((0, 0, debit_line_vals))
                credit_line_vals = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': move.date,
                    'partner_id': partner_id,
                    'credit': valuation_amount > 0 and valuation_amount + bom_cost_price or 0,
                    'debit': valuation_amount < 0 and -valuation_amount or 0,
                    'account_id': credit_account_id,
                }
                bom_cost_list.append((0, 0, credit_line_vals))
                return bom_cost_list
        else:
            return super(qdodoo_stock_quant_inherit, self)._prepare_account_move_line(cr, uid, move, qty, cost,
                                                                                      credit_account_id,
                                                                                      debit_account_id, context=context)
            # def _prepare_account_move_line(self, cr, uid, move, qty, cost, credit_account_id, debit_account_id, context=None):
            #     """
            #     Generate the account.move.line values to post to track the stock valuation difference due to the
            #     processing of the given quant.
            #     """
            #     location_model_us, location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock',
            #                                                                                          'location_production')
            #     if context is None:
            #         context = {}
            #
            #     if move.location_dest_id.id == location_id:
            #         produce_ids = self.pool.get("mrp.production").search(cr, uid, [('name', '=', move.name)])
            #         mrp_obj = self.pool.get("mrp.production").browse(cr, uid, produce_ids[0])
            #
            #         currency_obj = self.pool.get('res.currency')
            #         if context.get('force_valuation_amount'):
            #             valuation_amount = context.get('force_valuation_amount')
            #         else:
            #             if move.product_id.cost_method == 'average':
            #                 valuation_amount = cost if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal' else move.product_id.standard_price
            #             else:
            #                 valuation_amount = cost if move.product_id.cost_method == 'real' else move.product_id.standard_price
            #         # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
            #         # the company currency... so we need to use round() before creating the accounting entries.
            #         valuation_amount = currency_obj.round(cr, uid, move.company_id.currency_id, valuation_amount * qty)
            #         partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(
            #             move.picking_id.partner_id).id) or False
            #         debit_line_vals = {
            #             'name': move.name,
            #             'product_id': mrp_obj.product_id.id,
            #             'quantity': qty,
            #             'product_uom_id': move.product_id.uom_id.id,
            #             'ref': move.picking_id and move.picking_id.name or False,
            #             'date': move.date,
            #             'partner_id': partner_id,
            #             'debit': valuation_amount > 0 and valuation_amount or 0,
            #             'credit': valuation_amount < 0 and -valuation_amount or 0,
            #             'account_id': debit_account_id,
            #         }
            #         credit_line_vals = {
            #             'name': move.name,
            #             'product_id': move.product_id.id,
            #             'quantity': qty,
            #             'product_uom_id': move.product_id.uom_id.id,
            #             'ref': move.picking_id and move.picking_id.name or False,
            #             'date': move.date,
            #             'partner_id': partner_id,
            #             'credit': valuation_amount > 0 and valuation_amount or 0,
            #             'debit': valuation_amount < 0 and -valuation_amount or 0,
            #             'account_id': credit_account_id,
            #         }
            #         return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
            #
            #     else:
            #
            #         return super(qdodoo_stock_quant_inherit, self)._prepare_account_move_line(cr, uid, move, qty, cost,
            #                                                                                   credit_account_id,
            #                                                                                   debit_account_id,
            #                                                                                   context=context)
