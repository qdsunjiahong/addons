# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, api, fields, _
from openerp.osv import osv

class qdodoo_product_product_inherit(models.Model):
    """
        在产品中增加按照批次价格出库标识字段
    """

    _inherit = 'product.template'

    user_lot_price = fields.Boolean(u'按照批次价格出库')

class qdodoo_stock_production_lot_inherit(models.Model):
    """
        在批次中增加价格、合计数量字段
    """

    _inherit = 'stock.production.lot'

    price_unit = fields.Float(u'价格')

class qdodoo_stock_transfer_details_inherit(models.Model):
    """
       转移时，针对批次价格的处理
    """

    _inherit = 'stock.transfer_details'

    # 采购入库时校验，只能选择相同产品、价格的批次
    @api.one
    def do_detailed_transfer(self):
        quant_obj = self.env['stock.quant']
        account_line_obj = self.env['account.move.line']
        res = super(qdodoo_stock_transfer_details_inherit, self).do_detailed_transfer()
        account_ids = self.env['account.move'].search([('ref','=',self.picking_id.name)])
        for line in self.item_ids:
            # 判断产品是否要求按照批次价格出库
            if line.product_id.user_lot_price:
                # 如果是采购入库，并且有批次
                if line.lot_id and line.sourceloc_id.usage == 'supplier':
                    # 如果有批次价格
                    if line.lot_id.price_unit:
                        # 判断批次单价是否是产品的采购单价格
                        for move_line in line.packop_id.linked_move_operation_ids:
                            if move_line.move_id.price_unit != line.lot_id.price_unit:
                                raise osv.except_osv(_(u'警告'),_(u'此次入库的价格和选择批次的价格不符，请检查批次！'))
                    else:
                        # 更新产品的批次价格
                        line.lot_id.write({'price_unit':line.packop_id.linked_move_operation_ids[0].move_id.price_unit})
                # 如果是出库、运输库位出入库，并且有批次，按照批次价格修改对应的
                if line.lot_id and line.lot_id.price_unit and (line.destinationloc_id.usage in ('customer','transit') or line.sourceloc_id.usage == 'transit'):
                    # 判断该批次、此库位中是否有足够的产品出库
                    # 查询该库位该批次的库存
                    all_num = 0
                    quant_ids = quant_obj.search([('lot_id','=',line.lot_id.id),('location_id','=',line.sourceloc_id.id)])
                    for quant_id in quant_ids:
                        all_num += quant_id.qty
                    if all_num < line.quantity:
                        raise osv.except_osv(_(u'错误'),_(u'该批次中此库位的库存数量不足，请重新选择批次！'))
                    for move_line in line.packop_id.linked_move_operation_ids:
                        move_line.move_id.write({'price_unit':line.lot_id.price_unit})
                    # 查找库位移动产生的凭证
                    account_line_ids = account_line_obj.search([('name','=',line.product_id.name),('move_id','in',account_ids.ids)])
                    for account_line_id in account_line_ids:
                        if account_line_id.debit > 0:
                            account_line_id.write({'debit':account_line_id.quantity*line.lot_id.price_unit})
                        if account_line_id.credit > 0:
                            account_line_id.write({'credit':account_line_id.quantity*line.lot_id.price_unit})
        return res

class qdodoo_stock_quant_inherit(models.Model):
    """
        修改库存估值，按照批次的价格计算
    """

    _inherit = 'stock.quant'

    new_inventory_value = fields.Float(u'存货价值',compute="_get_new_inventory_value")

    # 增加分支，如果有批次价格按照批次价格计算
    def _get_new_inventory_value(self):
        res = {}
        uid_company_id = self.env['res.users'].browse(self._uid).company_id.id
        for quant in self:
            if quant.lot_id and quant.lot_id.price_unit:
                quant.new_inventory_value = quant.lot_id.price_unit * quant.qty
            else:
                if quant.company_id.id != uid_company_id:
                    users = self.env['res.users'].search([('company_id','=',quant.company_id.id)])
                    quant = self.browse(self._cr, users[0].id, quant.id)
                quant.new_inventory_value = self._get_inventory_value(quant)
        return res

class qdodoo_mrp_product_produce_inherit(models.Model):
    """
        生产选择批次，修改产品的成本价
    """

    _inherit = 'mrp.product.produce'

    @api.multi
    def do_produce(self):
        # 判断产成品是否启用批次价格
        if self.product_id.user_lot_price:
            # 判断产成品的价格计算方法，获取批次价格
            product_obj = self.pool['product.product']
            mrp_obj = self.env['mrp.production']
            account_line_obj = self.env['account.move.line']
            if self.product_id.cost_method == 'average':
                # 根据投料自动计算
                sum = 0.0
                for line in self.consume_lines:
                    if line.lot_id and line.lot_id.price_unit:
                        sum += line.lot_id.price_unit * line.product_qty
                    else:
                        users = self.env['res.users'].search([('company_id','=',line.product_id.company_id.id)])
                        sum += product_obj.browse(self._cr, users[0].id, line.product_id.id).standard_price * line.product_qty
                new_price = sum / self.product_qty
            else:
                # 获取产品当前的成本价
                users = self.env['res.users'].search([('company_id','=',self.product_id.company_id.id)])
                new_price = product_obj.browse(self._cr, users[0].id, self.product_id.id).standard_price
            # 判断批次是否正确
            if self.lot_id.price_unit:
                if self.lot_id.price_unit != new_price:
                    raise osv.except_osv(_(u'警告'),_(u'选择的批次价格和当前产成本价格不符！'))
            else:
                # 更新批次的价格
                self.lot_id.write({'price_unit':new_price})
        res = super(qdodoo_mrp_product_produce_inherit, self).do_produce()
        # 修改产成品的stock.move的单价
        mrp_id = mrp_obj.browse(self._context.get('active_id'))
        for line in mrp_id.move_created_ids2:
            line.write({'product_price':new_price})
            # 查找对应的分录，修改价格
            account_line_ids = account_line_obj.search([('name','=',mrp_id.name),('product_id','=',mrp_id.product_id.id)])
            for account_line_id in account_line_ids:
                if account_line_id.debit > 0:
                    account_line_id.write({'debit':account_line_id.quantity*new_price})
                if account_line_id.credit > 0:
                    account_line_id.write({'credit':account_line_id.quantity*new_price})
        # 修改原料的stock.move的单价
        for line in mrp_id.move_lines2:
            if line.restrict_lot_id and line.restrict_lot_id.price_unit:
                line.write({'product_price':line.restrict_lot_id.price_unit})
                # 查找对应的分录，修改价格
                account_line_ids = account_line_obj.search([('name','=',mrp_id.name),('product_id','=',line.product_id.id)])
                for account_line_id in account_line_ids:
                    if account_line_id.debit > 0:
                        account_line_id.write({'debit':account_line_id.quantity*line.restrict_lot_id.price_unit})
                    if account_line_id.credit > 0:
                        account_line_id.write({'credit':account_line_id.quantity*line.restrict_lot_id.price_unit})
        return res

class qdodoo_stock_inventory_inherit(models.Model):
    """
        库存盘点产生价格按照批次价格
    """
    _inherit = 'stock.inventory'

    @api.one
    def action_done(self):
        res = super(qdodoo_stock_inventory_inherit, self).action_done()
        move_obj = self.env['stock.move']
        account_line_obj = self.env['account.move.line']
        account_line_lst = []
        for line in self.line_ids:
            # 判断产品是否要求按照批次价格出库
            if line.product_id.user_lot_price:
                if line.prod_lot_id and line.prod_lot_id.price_unit:
                    # 计算盘点数量
                    diff_num = line.product_qty - line.theoretical_qty
                    if abs(diff_num) > 0:
                        # 查询对应的的盘点盈亏
                        move_ids = move_obj.search([('name','=','INV:'+self.name),('product_id','=',line.product_id.id),('product_uom_qty','=',abs(diff_num)),('price_unit','!=',line.prod_lot_id.price_unit)])
                        if move_ids:
                            move_ids[0].write({'price_unit':line.prod_lot_id.price_unit})
                        # 查询对应的凭证
                        account_line_ids = account_line_obj.search([('name','=','INV:'+self.name),('product_id','=',line.product_id.id),('quantity','=',abs(diff_num)),('id','not in',account_line_lst)])
                        lengh = 0
                        for account_line_id in account_line_ids:
                            all_price = account_line_id.quantity*line.prod_lot_id.price_unit
                            if account_line_id.debit > 0 and account_line_id.debit != all_price:
                                account_line_id.write({'debit':all_price})
                                lengh += 1
                                account_line_lst.append(account_line_id.id)
                            if account_line_id.credit > 0 and account_line_id.credit != all_price:
                                account_line_id.write({'credit':all_price})
                                lengh += 1
                                account_line_lst.append(account_line_id.id)
                            if lengh >= 2:
                                break
        return res