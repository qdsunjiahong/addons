# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api,_
from openerp.osv import osv
from datetime import datetime
from openerp import SUPERUSER_ID
from openerp.tools.float_utils import float_compare
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time


class qdodoo_account_invoice(models.Model):
    _inherit = 'stock.invoice.onshipping'

    def _compute_date(self):
        return fields.date.today()

    invoice_date = fields.Date(string=u'发票日期', default=_compute_date)

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        if context is None:
            context = {}
        partner, currency_id, company_id, user_id = key
        print key, inv_type
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
            print account_id
            payment_term = partner.property_payment_term.id or False
        else:
            account_id = partner.property_account_payable.id
            payment_term = partner.property_supplier_payment_term.id or False
        if payment_term:
            pterm = self.pool.get('account.payment.term').browse(cr, uid, payment_term)
            pterm_list = pterm.compute(value=1, date_ref=context.get('date_inv', []))
            if pterm_list:
                date_due = max(line[0] for line in pterm_list[0])
            else:
                date_due = False
            return {
                'origin': move.picking_id.name,
                'date_invoice': context.get('date_inv', False),
                'date_due': date_due,
                'user_id': user_id,
                'partner_id': partner.id,
                'account_id': account_id,
                'payment_term': payment_term,
                'type': inv_type,
                'fiscal_position': partner.property_account_position.id,
                'company_id': company_id,
                'currency_id': currency_id,
                'journal_id': journal_id,
                'group_ref': move.picking_id.group_id.name
            }
        else:
            return {
                'origin': move.picking_id.name,
                'date_invoice': context.get('date_inv', False),
                'date_due': False,
                'user_id': user_id,
                'partner_id': partner.id,
                'account_id': account_id,
                'payment_term': payment_term,
                'type': inv_type,
                'fiscal_position': partner.property_account_position.id,
                'company_id': company_id,
                'currency_id': currency_id,
                'journal_id': journal_id,
                'group_ref': move.picking_id.group_id.name
            }

class qdodoo_stock_picking(models.Model):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                }
                if prod.packop_id:
                    prod.packop_id.with_context(no_recompute=True).write(pack_datas)
                    processed_ids.append(prod.packop_id.id)
                else:
                    pack_datas['picking_id'] = self.picking_id.id
                    packop_id = self.env['stock.pack.operation'].create(pack_datas)
                    processed_ids.append(packop_id.id)
        # Delete the others
        packops = self.env['stock.pack.operation'].search(
            ['&', ('picking_id', '=', self.picking_id.id), '!', ('id', 'in', processed_ids)])
        packops.unlink()
        self.picking_id.do_transfer()
        # 修改对应的凭证的金额
        account_id = self.env['account.move'].search([('ref','=',self.picking_id.name)])
        # 判断是否是产品费用产生的调拨单
        expense_id = self.env['product.expense'].search([('name','=',self.picking_id.origin)])
        if expense_id:
            for line_key in account_id:
                for line1 in line_key.line_id:
                    # 获取对应的调拨明细
                    stock_move_ids = self.env['stock.move'].search([('picking_id','=',self.picking_id.id),('product_id','=',line1.product_id.id)])
                    for stock_move_ids in stock_move_ids:
                        price = stock_move_ids.price_unit*line1.quantity
                        if line1.credit:
                            line1.write({'credit':price})
                        if line1.debit:
                            line1.write({'debit':price})
        # 修改对应的凭证的辅助核算项
        # 先判断原单据如果是销售订单
        analytic = ''
        sale_id = self.env['sale.order'].search([('name','=',self.picking_id.origin)])
        if sale_id:
            analytic = sale_id.project_id.id
        else:
            # 判断是否仍然是出库单
            res = self.env['stock.picking'].search([('name','=',self.picking_id.origin)])
            while res:
                sale_id = self.env['sale.order'].search([('name','=',res[0].origin)])
                if sale_id:
                    analytic = sale_id.project_id.id
                    break
                else:
                    res = self.env['stock.picking'].search([('name','=',res[0].origin)])
            # 获取到辅助核算项，更新对应的凭证中的辅助核算项
            # 查询对应的凭证
        if analytic:
            for key in account_id:
                for line in key.line_id:
                    line.write({'analytic_account_id':analytic})
        #####创建发票
        ite_obj = self.item_ids[0]
        location_model_cus, lo_id = self.env['ir.model.data'].get_object_reference('stock', 'stock_location_suppliers')
        location_model_cus2, lo_id2 = self.env['ir.model.data'].get_object_reference('stock',
                                                                                     'stock_location_customers')
        if self.picking_id.acc:
            if ite_obj.sourceloc_id.id in (lo_id, lo_id2) and self.picking_id.invoice_state == '2binvoiced':
                onshipping_id = self.env['stock.invoice.onshipping'].create({'invoice_date': self.picking_id.date_done})
                onshipping_id.create_invoice()
            elif ite_obj.destinationloc_id.id in (lo_id, lo_id2) and self.picking_id.invoice_state == '2binvoiced':
                onshipping_id = self.env['stock.invoice.onshipping'].create({'invoice_date': self.picking_id.date_done})
                onshipping_id.create_invoice()
            return True
        if ite_obj.sourceloc_id.id in (lo_id, lo_id2) and self.picking_id.invoice_state == '2binvoiced':
            onshipping_id = self.env['stock.invoice.onshipping'].create({'invoice_date': fields.date.today()})
            onshipping_id.create_invoice()
        elif ite_obj.destinationloc_id.id in (lo_id, lo_id2) and self.picking_id.invoice_state == '2binvoiced':
            onshipping_id = self.env['stock.invoice.onshipping'].create({'invoice_date': fields.date.today()})
            onshipping_id.create_invoice()
        return True

class qdodoo_stock_move_inherit_tfs(models.Model):
    _inherit = 'stock.move'

    tfs_price_unit = fields.Float(u'成本价')

    def action_done(self, cr, uid, ids, context=None):
        """ Process completely the moves given as ids and if all moves are done, it will finish the picking.
        """
        context = context or {}
        picking_obj = self.pool.get("stock.picking")
        quant_obj = self.pool.get("stock.quant")
        operation_line_obj = self.pool.get("stock.move.operation.link")
        unlink_lst = []
        todo = [move.id for move in self.browse(cr, uid, ids, context=context) if move.state == "draft"]
        if todo:
            ids = self.action_confirm(cr, uid, todo, context=context)
        pickings = set()
        procurement_ids = set()
        #Search operations that are linked to the moves
        operations = set()
        move_qty = {}
        for move in self.browse(cr, uid, ids, context=context):
            move_qty[move.id] = move.product_qty
            for link in move.linked_move_operation_ids:
                operations.add(link.operation_id)

        #Sort operations according to entire packages first, then package + lot, package only, lot only
        operations = list(operations)
        operations.sort(key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (x.lot_id and -1 or 0))

        for ops in operations:
            if ops.picking_id:
                pickings.add(ops.picking_id.id)
            main_domain = [('qty', '>', 0)]
            for record in ops.linked_move_operation_ids:
                move = record.move_id
                self.check_tracking(cr, uid, move, not ops.product_id and ops.package_id.id or ops.lot_id.id, context=context)
                prefered_domain = [('reservation_id', '=', move.id)]
                fallback_domain = [('reservation_id', '=', False)]
                fallback_domain2 = ['&', ('reservation_id', '!=', move.id), ('reservation_id', '!=', False)]
                prefered_domain_list = [prefered_domain] + [fallback_domain] + [fallback_domain2]
                dom = main_domain + self.pool.get('stock.move.operation.link').get_specific_domain(cr, uid, record, context=context)
                quants = quant_obj.quants_get_prefered_domain(cr, uid, ops.location_id, move.product_id, record.qty, domain=dom, prefered_domain_list=prefered_domain_list,
                                                          restrict_lot_id=move.restrict_lot_id.id, restrict_partner_id=move.restrict_partner_id.id, context=context)
                if ops.product_id:
                    #If a product is given, the result is always put immediately in the result package (if it is False, they are without package)
                    quant_dest_package_id  = ops.result_package_id.id
                    ctx = context
                else:
                    # When a pack is moved entirely, the quants should not be written anything for the destination package
                    quant_dest_package_id = False
                    ctx = context.copy()
                    ctx['entire_pack'] = True
                quant_obj.quants_move(cr, uid, quants, move, ops.location_dest_id, location_from=ops.location_id, lot_id=ops.lot_id.id, owner_id=ops.owner_id.id, src_package_id=ops.package_id.id, dest_package_id=quant_dest_package_id, context=ctx)

                # Handle pack in pack
                if not ops.product_id and ops.package_id and ops.result_package_id.id != ops.package_id.parent_id.id:
                    self.pool.get('stock.quant.package').write(cr, SUPERUSER_ID, [ops.package_id.id], {'parent_id': ops.result_package_id.id}, context=context)
                if not move_qty.get(move.id):
                    unlink_lst.append(record.id)
                    # raise osv.except_osv(_("Error"), _("The roundings of your Unit of Measures %s on the move vs. %s on the product don't allow to do these operations or you are not transferring the picking at once. ") % (move.product_uom.name, move.product_id.uom_id.name))
                else:
                    move_qty[move.id] -= record.qty
        #Check for remaining qtys and unreserve/check move_dest_id in
        move_dest_ids = set()
        for move in self.browse(cr, uid, ids, context=context):
            move_qty_cmp = float_compare(move_qty[move.id], 0, precision_rounding=move.product_id.uom_id.rounding)
            if move_qty_cmp > 0:  # (=In case no pack operations in picking)
                main_domain = [('qty', '>', 0)]
                prefered_domain = [('reservation_id', '=', move.id)]
                fallback_domain = [('reservation_id', '=', False)]
                fallback_domain2 = ['&', ('reservation_id', '!=', move.id), ('reservation_id', '!=', False)]
                prefered_domain_list = [prefered_domain] + [fallback_domain] + [fallback_domain2]
                self.check_tracking(cr, uid, move, move.restrict_lot_id.id, context=context)
                qty = move_qty[move.id]
                quants = quant_obj.quants_get_prefered_domain(cr, uid, move.location_id, move.product_id, qty, domain=main_domain, prefered_domain_list=prefered_domain_list, restrict_lot_id=move.restrict_lot_id.id, restrict_partner_id=move.restrict_partner_id.id, context=context)
                quant_obj.quants_move(cr, uid, quants, move, move.location_dest_id, lot_id=move.restrict_lot_id.id, owner_id=move.restrict_partner_id.id, context=context)

            # If the move has a destination, add it to the list to reserve
            if move.move_dest_id and move.move_dest_id.state in ('waiting', 'confirmed'):
                move_dest_ids.add(move.move_dest_id.id)

            if move.procurement_id:
                procurement_ids.add(move.procurement_id.id)

            #unreserve the quants and make them available for other operations/moves
            quant_obj.quants_unreserve(cr, uid, move, context=context)
        # Check the packages have been placed in the correct locations
        self._check_package_from_moves(cr, uid, ids, context=context)
        #set the move as done
        self.write(cr, uid, ids, {'state': 'done', 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
        self.pool.get('procurement.order').check(cr, uid, list(procurement_ids), context=context)
        #assign destination moves
        if move_dest_ids:
            self.action_assign(cr, uid, list(move_dest_ids), context=context)
        #check picking state to set the date_done is needed
        done_picking = []
        for picking in picking_obj.browse(cr, uid, list(pickings), context=context):
            if picking.state == 'done' and not picking.date_done:
                done_picking.append(picking.id)
        if done_picking:
            picking_obj.write(cr, uid, done_picking, {'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
        if unlink_lst:
            operation_line_obj.unlink(cr, uid, unlink_lst)
        return True

    def create(self, cr, uid, valus, context=None):
        product_obj = self.pool.get('product.product')
        users_obj = self.pool.get('res.users')
        expense_obj = self.pool.get('product.expense')
        expense_line_obj = self.pool.get('product.expense.line')
        if valus.get('product_id'):
            expense_ids = expense_obj.search(cr, uid, [('name','=',valus.get('name'))])
            if expense_ids:
                # 获取对应的明细
                expense_line_ids = expense_line_obj.search(cr, uid, [('expense_id','in',expense_ids),('product','=',valus.get('product_id'))])
                if expense_line_ids:
                    valus['tfs_price_unit'] = expense_line_obj.browse(cr, uid, expense_line_ids[0]).price
                    valus['price_unit'] = expense_line_obj.browse(cr, uid, expense_line_ids[0]).price
            else:
                # 获取产品公司id
                company_id = product_obj.browse(cr, uid, valus.get('product_id')).company_id.id
                # 查询该公司的人
                company_uid = users_obj.search(cr, uid, [('company_id', '=', company_id)])
                if not company_uid:
                    raise osv.except_osv('错误', "该产品所属的公司没有用户!'")
                else:
                    valus['tfs_price_unit'] = product_obj.browse(cr, company_uid[0], valus.get('product_id')).standard_price
        return super(qdodoo_stock_move_inherit_tfs, self).create(cr, uid, valus, context=context)

    def write(self, cr, uid, ids, valus, context=None):
        if isinstance(ids, (int,long)):
            ids = [ids]
        product_obj = self.pool.get('product.product')
        users_obj = self.pool.get('res.users')
        expense_obj = self.pool.get('product.expense')
        expense_line_obj = self.pool.get('product.expense.line')
        if valus.get('product_id'):
            name = self.browse(cr, uid, ids[0])
            expense_ids = expense_obj.search(cr, uid, [('name','=',name)])
            if expense_ids:
                # 获取对应的明细
                expense_line_ids = expense_line_obj.search(cr, uid, [('expense_id','in',expense_ids),('product','=',valus.get('product_id'))])
                if expense_line_ids:
                    valus['tfs_price_unit'] = expense_line_obj.browse(cr, uid, expense_line_ids[0]).price
                    valus['price_unit'] = expense_line_obj.browse(cr, uid, expense_line_ids[0]).price
            else:
                # 获取产品公司id
                company_id = product_obj.browse(cr, uid, valus.get('product_id')).company_id.id
                # 查询该公司的人
                company_uid = users_obj.search(cr, uid, [('company_id', '=', company_id)])
                if not company_uid:
                    raise osv.except_osv('错误', "该产品所属的公司没有用户!'")
                else:
                    valus['tfs_price_unit'] = product_obj.browse(cr, company_uid[0], valus.get('product_id')).standard_price
        return super(qdodoo_stock_move_inherit_tfs, self).write(cr, uid, ids, valus, context=context)