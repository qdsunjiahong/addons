# -*- coding: utf-8 -*-
###########################################################################################
#
#    account.sales.state for Odoo8.0
#    Copyright (C) 2016 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields, api, _
insert_ids_list = []

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
        # 查询产品模板ID对应的物料清单ID
        product_bom_dict = {}
        for bom_id in self.env['mrp.bom'].search([]):
            product_bom_dict[bom_id.product_tmpl_id] = bom_id
        #时间范围
        start_date = self.check_date + " 00:00:01"
        end_date = self.check_date + " 23:59:59"
        #查找时间范围内指定生产车间的生产订单
        mrp_production_ids = self.env['mrp.production'].search([('state','=','confirmed'),('analytic_account', '=', self.account_analytic_id.id), ('date_finished', '>=', start_date), ('date_finished', '<=', end_date)])
        # 记录bom的数据{产品:产成品数量}
        bom_dict = {}
        for mrp_production in mrp_production_ids:
            # 是否已存在产成品
            if mrp_production.product_id in bom_dict:
                bom_dict[mrp_production.product_id] += mrp_production.product_qty
            else:
                bom_dict[mrp_production.product_id] = mrp_production.product_qty
            for line in mrp_production.bom_id.bom_line_ids:
                bom_id = product_bom_dict.get(line.product_id.product_tmpl_id)
                if bom_id:
                    if line.product_id in bom_dict:
                        bom_dict[line.product_id] += line.product_qty
                    else:
                        bom_dict[line.product_id] = line.product_qty
        # 插入对应数据
        insert_ids_list = []
        for key, value in bom_dict.items():
            for line in product_bom_dict[key.product_tmpl_id].bom_line_ids:
                # 隐藏的分类产品不显示
                if not line.product_id.categ_id.is_descreption:
                    stock_product_id = line.product_id.id
                    stock_qty = line.product_qty * value / product_bom_dict[key.product_tmpl_id].product_qty
                    res_id = report_obj.create({'product_id':key.id,'production_qty':value,'stock_product_id':stock_product_id,'stock_qty':stock_qty})
                    insert_ids_list.append(res_id.id)
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

class qdodoo_product_category_tfs(models.Model):
    _inherit = 'product.category'

    # 增加字段判断是否要在生产投料报表中展示该分类产品
    is_descreption = fields.Boolean(u'该分类产品是否在生产投料报表中隐藏')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
