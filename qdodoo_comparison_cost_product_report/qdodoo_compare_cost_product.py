# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _, tools
from openerp.exceptions import except_orm


class qdodoo_compare_product_cost_report(models.Model):
    _name = 'compare.product.cost'

    product_id = fields.Many2one('product.product', string=u'产品名称')
    product_qty = fields.Float(digits=(16, 2), string=u'数量')
    location_id = fields.Many2one('stock.location', string=u'库位')
    assistant_id = fields.Many2one('account.analytic.account', string=u'辅助核算')
    actual_amount = fields.Float(digits=(16, 4), string=u'实际金额')
    actual_price = fields.Float(digits=(16, 4), string=u'实际单价')
    theoretical_amount = fields.Float(digits=(16, 4), string=u'理论金额')
    theoretical_price = fields.Float(digits=(16, 4), string=u'理论单价')
    save_amount = fields.Float(digits=(16, 4), string=u'节约金额')
    price_save = fields.Float(digits=(16, 4), string=u'单份节约金额')
    amount_difference_rate = fields.Char(string=u'金额差异率')


class qdodoo_search_compare_product_cost(models.Model):
    _name = 'qdodoo.search.compare.product.cost'

    date_start = fields.Date(string=u'开始时间', required=True)
    date_end = fields.Date(string=u'结束时间', required=True)
    location_id = fields.Many2one('stock.location', required=True)

    @api.multi
    def btn_search(self):
        mrp_obj = self.env['mrp.production']
        if self.date_start and self.date_end:
            datetime_start = self.date_start + " 00:00:01"
            datetime_end = self.date_end + " 23:59:29"
            mrp_ids = mrp_obj.search([('date_planned', '>=', datetime_start), ('state', '=', 'done'),
                                      ('location_dest_id', '=', self.location_id.id)])
            result_ids = []
            if mrp_ids:
                for mrp_id in mrp_ids:
                    sql = """
                        select
                            mp.id as id,
                            mp.product_id as product_id,
                            mp.product_qty as product_qty,
                            mp.analytic_account as assistant_id,
                            sm.price_unit as price_unit,
                            sm.product_uom_qty as product_uom_qty,
                            mppl.product_qty as product_qty2
                        from mrp_production mp
                            LEFT JOIN stock_move sm ON sm.raw_material_production_id = %s
                            LEFT JOIN mrp_production_product_line mppl ON mppl.production_id = %s and mppl.product_id = sm.product_id
                        where mp.id=%s and mp.state='done' and sm.product_uom_qty>0 and mp.date_planned >= '%s' and mp.date_planned <= '%s'
                        """ % (mrp_id.id, mrp_id.id, mrp_id.id, datetime_start, datetime_end)

                    self.env.cr.execute(sql)
                    result = self.env.cr.fetchall()
                    product_id = False
                    product_qty = 0
                    actual_amount = 0
                    theoretical_amount = 0
                    assistant_id = False
                    print result
                    if result:
                        for i in result:
                            mp_id, product_id1, product_qty1, assistant_id1, price_unit1, product_uom_qty1, product_qty_2 = i
                            if not product_qty_2:
                                product_qty_2 = 0
                            product_id = product_id1
                            product_qty += product_qty1
                            assistant_id = assistant_id1
                            actual_amount += price_unit1 * product_uom_qty1
                            theoretical_amount = theoretical_amount + price_unit1 * product_qty_2
                        data = {
                            'product_id': product_id,
                            'product_qty': product_qty,
                            'location_id': self.location_id.id,
                            'assistant_id': assistant_id,
                            'actual_amount': actual_amount,
                            'actual_price': actual_amount / mrp_id.product_qty,
                            'theoretical_amount': theoretical_amount,
                            'theoretical_price': theoretical_amount / mrp_id.product_qty,
                            'save_amount': actual_amount - theoretical_amount,
                            'price_save': (actual_amount - theoretical_amount) / mrp_id.product_qty,
                            'amount_difference_rate': str('%.4f' %
                                                          ((
                                                               actual_amount - theoretical_amount) / theoretical_amount * 100)) + "%",
                        }

                        create_obj = self.env['compare.product.cost'].create(data)
                        result_ids.append(create_obj.id)
                    else:
                        raise except_orm(_(u'警告'), _(u'为查询到数据'))
                view_model, view_id = self.env['ir.model.data'].get_object_reference(
                    'qdodoo_comparison_cost_product_report', 'qdodoo_compare_cost_report_tree')
                return {
                    'name': (u'产品标准原料成本与实际成本对比汇总表'),
                    'view_type': 'form',
                    "view_mode": 'tree',
                    'res_model': 'compare.product.cost',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', result_ids)],
                    'views': [(view_id, 'tree')],
                    'view_id': [view_id],
                }
