# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_stock_in_analytic_report(models.Model):
    """
    入库分析表
    """
    _name = 'qdodoo.stock.in.analytic.report'
    _description = 'qdodoo.stock.in.analytic.report'

    _order = 'period_id'
    date = fields.Date(string=u'日期')
    year = fields.Char(string=u'年度')
    period_id = fields.Char(string=u'月份')
    quarter = fields.Char(string=u'季度')
    partner_id = fields.Many2one('res.partner', string=u'供应商')
    product_id = fields.Char(string=u'产品')
    default_code = fields.Char(string=u'产品编号')
    product_qty = fields.Float(string=u'数量')
    price_unit = fields.Float(string=u'单价', digits=(16, 4))
    product_amount = fields.Float(string=u'金额')
    location_id = fields.Many2one('stock.location', string=u'交货地点')
    company_id = fields.Many2one('res.company', string=u'公司')
    property_supplier_payment_term = fields.Many2one('account.payment.term', string=u'付款条款')
    uom_id = fields.Many2one('product.uom', string=u'单位')

# class qdodoo_stock_in_analytic_report2(models.Model):
#     """
#     入库分析表合计
#     """
#     _name = 'qdodoo.stock.in.analytic.report2'
#     _description = 'qdodoo.stock.in.analytic.report2'
#
#     _order = 'period_id'
#     date = fields.Date(string=u'日期')
#     year = fields.Char(string=u'年度')
#     period_id = fields.Char(string=u'月份')
#     quarter = fields.Char(string=u'季度')
#     partner_id = fields.Many2one('res.partner', string=u'供应商')
#     product_id = fields.Char(string=u'产品')
#     default_code = fields.Char(string=u'产品编号')
#     product_qty = fields.Float(string=u'数量')
#     uom_id = fields.Many2one('product.uom', string=u'单位')
#     price_unit = fields.Float(string=u'单价', digits=(16, 4))
#     product_amount = fields.Float(string=u'金额')
#     property_supplier_payment_term = fields.Char(string=u'付款条款')
#         sql_l = """
#             select
#                 af.name as af_name,
#                 ai.partner_id as partner_id,
#                 pp.name_template as product_name,
#                 pp.default_code as default_code,
#                 ail.quantity as product_qty,
#                 ail.price_unit as price_unit,
#                 (ail.price_unit * ail.quantity) as product_amount,
#                 pt.uom_po_id as uom_id,
#                 po.location_id as location_id,
#                 po.payment_term_id as payment_term_id,
#                 ail.company_id as company_id
#             from account_invoice_line ail
#                 LEFT JOIN product_product pp ON pp.id = ail.product_id
#                 LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
#                 LEFT JOIN purchase_invoice_rel pir ON pir.invoice_id = ail.invoice_id
#                 LEFT JOIN account_invoice ai ON ai.id = ail.invoice_id and pir.invoice_id=ai.id
#                 LEFT JOIN purchase_order po ON po.id = pir.purchase_id
#                 LEFT JOIN account_period ap ON ap.id = ai.period_id
#                 LEFT JOIN account_fiscalyear af ON af.id= ap.fiscalyear_id
#             where po.state = 'done' and ai.state != 'cancel'
#             """