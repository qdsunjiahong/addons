# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_mrp_practice_compare_theory(models.Model):
    _name = 'qdodoo.mrp.practice.compare.theory'
    _description = 'qdodoo.mrp.practice.compare.theory'

    product_id = fields.Many2one('product.product', string=u'产品')
    product_number = fields.Float(string=u'实际数量')
    product_number2 = fields.Float(string=u'计划数量')
    product_amount = fields.Float(string=u'实际金额')
    product_amount2 = fields.Float(string=u'理论金额')
    product_price = fields.Float(string=u'实际单价')
    product_price2 = fields.Float(string=u'理论单价')
    amount_compare = fields.Float(string=u'节约金额')
    unit_compare = fields.Float(string=u'单份节约金额')
    rate=fields.Char(string=u'金额差异率')
    location_id=fields.Many2one('stock.location',string=u'库位')
    line_ids = fields.One2many('mrp.practice.compare.theory.line', 'compare_id', string=u'明细')


class qdodoo_mrp_practice_compare_theory_line(models.Model):
    _name = 'mrp.practice.compare.theory.line'
    _description = 'mrp.practice.compare.theory.line'
    mp_id = fields.Many2one('mrp.production', string=u'生产单')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_number = fields.Float(string=u'实际数量')
    product_number2 = fields.Float(string=u'计划数量')
    product_amount = fields.Float(string=u'实际金额')
    product_amount2 = fields.Float(string=u'理论金额')
    product_price = fields.Float(string=u'实际单价')
    product_price2 = fields.Float(string=u'理论单价')
    amount_compare = fields.Float(string=u'节约金额')
    unit_compare = fields.Float(string=u'单份节约金额')
    rate=fields.Char(string=u'金额差异率')
    analytic_account=fields.Many2one('account.analytic.account',string=u'辅助核算项')
    compare_id = fields.Many2one('qdodoo.mrp.practice.compare.theory')
