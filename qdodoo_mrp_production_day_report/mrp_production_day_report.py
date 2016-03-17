# -*- coding: utf-8 -*-
###########################################################################################
#
#    account.sales.state for Odoo8.0
#    Copyright (C) 2016 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields, api, _

class qdodoo_mrp_production_day_report_search(models.Model):
    """
    用于弹出搜索并执行的model
    """
    _name = 'qdodoo.mrp.production.day.report.search'
    _description = u'查看每天生产投料报表'

    check_date = fields.Date(string=u'查看日期', required=True, default=fields.Date.today())
    account_analytic_id = fields.Many2one('account.analytic.account', string=u'生产车间', required=True)

    @api.multi
    def search_mrp_production_day_report(self):
        """
        根据查询条件查询数据，填写qdodoo.mrp.production.day.report模型，再调用报表视图显示
        """
        #清除旧数据
        self._cr.execute('delete from qdodoo_mrp_production_day_report')

        report_obj = self.env['qdodoo.mrp.production.day.report']

        #时间范围
        start_date = self.check_date + " 00:00:01"
        end_date = self.check_date + " 23:59:59"

        #查找时间范围内指定生产车间的生产订单
        insert_ids_list = []
        mrp_production_ids = self.env['mrp.production'].search([('analytic_account', '=', self.account_analytic_id.id), ('date_finished', '>=', start_date), ('date_finished', '<=', end_date)])
        for mrp_production in mrp_production_ids:
            product_id = mrp_production.product_id
            product_qty = mrp_production.product_qty
            move_lines2 = mrp_production.move_lines2  #mrp.production模型中的move_lines2 = fields.One2many('stock.move', 'raw_material_production_id')

            #每个产成品对应的产量
            all_qty = 0  #本生产订单下所有产成品的总产量
            product_id2quantity = {}  #{产成品ID:产量}
            for produced_product in mrp_production.move_created_ids2:
                product_id = produced_product.product_id.id
                produced_qty = produced_product.product_qty

                all_qty += produced_qty

                if product_id not in product_id2quantity:
                    product_id2quantity[product_id] = produced_qty
                else:
                    product_id2quantity[product_id] += produced_qty

            #同一个投料数量累加
            stock_product_id2qty_dict = {}
            for move_lines2_id in move_lines2:
                if not move_lines2_id.state == 'done':
                    pass

                stock_product_id = move_lines2_id.product_id.id  #投料ID
                stock_qty = move_lines2_id.product_qty  #投料数量

                if stock_product_id not in stock_product_id2qty_dict:
                    stock_product_id2qty_dict[stock_product_id] = stock_qty
                else:
                    stock_product_id2qty_dict[stock_product_id] += stock_qty

            #循环该生产单下每个投料，再循环每个产成品，将投料数量按产成品产量比例分配到各产成品下，并存储数据
            for stock_product_id, stock_qty in stock_product_id2qty_dict.items():
                for product_id, produced_qty in product_id2quantity.items():
                    insert_dict = {
                        'product_id': product_id,  #产成品
                        'production_qty': produced_qty,  #本产成品产量
                        'stock_product_id': stock_product_id,  #物料ID
                        'stock_qty': stock_qty*produced_qty/all_qty  #投料数量 = 本投料总量 x 本产成品产量/该生产订单总产量
                    }

                    #存储数据
                    insert_obj = report_obj.create(insert_dict)
                    insert_ids_list.append(insert_obj.id)

        view_model, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_mrp_production_day_report',
                                                               'view_mrp_production_day_report_graph')
        return {
            'name': u'生产投料报表',
            'view_type': 'form',
            "view_mode": 'graph',
            'res_model': 'qdodoo.mrp.production.day.report',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', insert_ids_list)],
            'views': [(view_id, 'graph')],
            'view_id': [view_id],
        }


class qdodoo_mrp_production_day_report(models.Model):
    """
    报表数据
    """
    _name = "qdodoo.mrp.production.day.report"
    _description = u"每天生产投料报表"
    _rec_name = 'production_qty'
    _order = 'product_id desc'

    product_id = fields.Many2one('product.product', string=u'产品名称', readonly=True)
    production_qty = fields.Float(string=u'产量', digits=(20,6), readonly=True, default=None)
    stock_product_id = fields.Many2one('product.product', string=u'投料', readonly=True)
    stock_qty = fields.Float(string=u'投料量', digits=(20,6), readonly=True)




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
