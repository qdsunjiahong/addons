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

    @api.one
    def do_transfer(self):
        for ids in self:
            if ids.state == 'done':
                raise osv.osv(_(u'错误'),_(u'转移单已完成，请刷新页面！'))
        res = super(stock_picking, self).do_transfer()
        for ids in self:
            # 删除虚增的库存
            for line in ids.move_lines:
                quant_ids = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',line.location_dest_id.id)])
                for quant_id in quant_ids:
                    for move_id in quant_id.history_ids:
                        if move_id.state != 'done':
                            quant_id.unlink()
                            break
        return res

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        if context is None:
            context = {}
        partner, currency_id, company_id, user_id = key
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
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
        if self.picking_id.state == 'done':
            raise osv.osv(_(u'错误'),_(u'转移单已完成，请刷新页面！'))
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