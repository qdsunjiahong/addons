# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################


from openerp import models, fields


class qdodoo_mrp_bom_line_inherit(models.Model):
    ####生产bom增加字段
    _inherit = 'mrp.bom.line'

    unit_price = fields.Float(string=u'单价', digits=(16, 4), compute='_get_unit_price')

    def _get_unit_price(self):
        for line in self.browse(self.ids):
            if line.product_id:
                line.unit_price = line.product_id.standard_price

    def onchange_product_id(self, cr, uid, ids, product_id, product_qty=0, context=None):
        """ Changes UoM if product_id changes.
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        res = {}
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            res['value'] = {
                'product_uom': prod.uom_id.id,
                'product_uos_qty': 0,
                'product_uos': False,
                'unit_price': prod.standard_price
            }
            if prod.uos_id.id:
                res['value']['product_uos_qty'] = product_qty * prod.uos_coeff
                res['value']['product_uos'] = prod.uos_id.id
        return res


class qdodoo_mrp_subproduct_inherit(models.Model):
    ####生产bom增加字段
    _inherit = 'mrp.subproduct'
    proportion = fields.Float(string=u'所占比例', digits=(16, 4), required=True)

    _defaults = {
        'proportion': 0.0
    }


class qdodoo_bom_cost(models.Model):
    #####生产bom增加page，建立模型
    _name = 'qdodoo.bom.cost'

    name = fields.Many2one('product.product', string=u'产品', required=True)
    num = fields.Float(string=u'数量', digits=(16, 4), required=True)
    unit_price = fields.Float(string=u'单价', digits=(16, 4), compute='_get_unit_price')
    bom_id = fields.Many2one('mrp.bom', ondelet='cascade', string='bom')

    def _get_unit_price(self):
        for line in self.browse(self.ids):
            if line.name:
                line.unit_price = line.name.standard_price

    def onchange_product_id(self, cr, uid, ids, name, context=None):
        """ Changes UoM if product_id changes.
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        res = {}
        if name:
            prod = self.pool.get('product.product').browse(cr, uid, name, context=context)
            res['value'] = {
                'unit_price': prod.standard_price
            }
        return res

    _defaults = {
        'num': 0.0
    }


class qdodoo_mrp_bom_inherit(models.Model):
    _inherit = 'mrp.bom'

    def _get_unit_price(self):
        for line in self.browse(self.ids):
            if line.product_id:
                line.unit_price = line.product_id.standard_price

    bom_cost_ids = fields.One2many('qdodoo.bom.cost', 'bom_id', string=u'费用')
    price_unit = fields.Float(string=u'单价', digits=(16, 4), compute="_get_unit_price")


class qdodoo_stock_move(models.Model):
    _inherit = 'stock.move'

    tatol_move = fields.Float(string=u'总价', digits=(16, 4))

    def onchage_product_id(self, cr, uid, ids, product_id, context=None):
        res = {}
        res['value'] = {}
        if product_id:
            product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
            res['value']['price_unit'] = product_obj.standard_price
        return res


class qdodoo_mrp_production_inherit(models.Model):
    # 继承生产订单模型
    _inherit = 'mrp.production'

    def _qdodoo_get_total_price(self):
        move_price = 0
        cost_price = 0
        sub_proportion = 0
        for move_obj in self.move_lines2:
            product_obj = move_obj.product_id
            move_price += float("%.4f" % (move_obj.product_uom_qty)) * product_obj.standard_price
        bom_obj = self.bom_id
        if bom_obj.bom_cost_ids:
            for cost_obj in bom_obj.bom_cost_ids:
                cost_price += float("%.4f" % (cost_obj.name.standard_price)) * cost_obj.num
        if bom_obj.sub_products:
            for sub_obj in bom_obj.sub_products:
                sub_proportion += sub_obj.proportion
        self.qdodoo_total_price = (move_price + cost_price) * (1 - sub_proportion)

    def _qdodoo_get_unit_price(self):
        move_price = 0
        cost_price = 0
        sub_proportion = 0
        for move_obj in self.move_lines2:
            product_obj = move_obj.product_id
            move_price += move_obj.product_uom_qty * product_obj.standard_price
        bom_obj = self.bom_id
        if bom_obj.bom_cost_ids:
            for cost_obj in bom_obj.bom_cost_ids:
                cost_price += cost_obj.name.standard_price * cost_obj.num
        if bom_obj.sub_products:
            for sub_obj in bom_obj.sub_products:
                sub_proportion += sub_obj.proportion

        self.qdodoo_unit_pirce = (move_price + cost_price) * (1 - sub_proportion) / self.product_qty

    qdodoo_unit_pirce = fields.Float(string=u'单价', digits=(16, 4), compute='_qdodoo_get_unit_price')
    qdodoo_total_price = fields.Float(string=u'总价', digits=(16, 4), compute='_qdodoo_get_total_price')


class mrp_product_produce(models.Model):
    _inherit = "mrp.product.produce"

    def do_produce(self, cr, uid, ids, context=None):
        production_id = context.get('active_id', False)
        assert production_id, "Production Id should be specified in context as a Active ID."
        data = self.browse(cr, uid, ids[0], context=context)
        self.pool.get('mrp.production').action_produce(cr, uid, production_id,
                                                       data.product_qty, data.mode, data, context=context)
        # mrp_obj = self.pool.get('mrp.production').browse(cr, uid, production_id)
        # account_move_ids = self.pool.get('account.move.line').search(cr, uid,
        #                                                              [('name', '=', mrp_obj.name), ('credit', '>', 0)])
        # move_list = []
        # for line in self.pool.get("account.move.line").browse(cr, uid, account_move_ids):
        #     move_list.append(line.credit)
        # move_list.sort()
        # qdodoo_total_cost = move_list[-1]
        # print qdodoo_bom_cost, 1111111
        # unit_price = float(qdodoo_total_cost) / mrp_obj.product_qty
        move_price = 0
        cost_price = 0
        sub_proportion = 0
        mrp_obj = self.pool.get("mrp.production").browse(cr, uid, production_id)
        for move_obj in mrp_obj.move_lines2:
            product_obj = move_obj.product_id
            move_price += move_obj.product_uom_qty * product_obj.standard_price
        bom_obj = mrp_obj.bom_id
        if bom_obj.bom_cost_ids:
            for cost_obj in bom_obj.bom_cost_ids:
                cost_price += cost_obj.name.standard_price * cost_obj.num
        if bom_obj.sub_products:
            for sub_obj in bom_obj.sub_products:
                sub_proportion += sub_obj.proportion
        unit_price = float("%.4f" % (move_price + cost_price) * (1 - sub_proportion)) / self.produdct_qty
        mrp_obj.product_id.write({'standard_price': unit_price})
        return {}


class qdodoo_stock_quant_inherit(models.Model):
    _inherit = 'stock.quant'

    def _prepare_account_move_line(self, cr, uid, move, qty, cost, credit_account_id, debit_account_id, context=None):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        location_model_us, location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock',
                                                                                             'location_production')
        if context is None:
            context = {}

        if move.location_dest_id.id == location_id:
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
