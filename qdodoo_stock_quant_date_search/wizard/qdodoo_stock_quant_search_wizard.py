# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_stock_quant_search(models.Model):
    """
    总库存查询wizard视图
    """
    _name = 'qdodoo.stock.quant.search'
    _description = 'qdodoo.stock.quant.search'

    date = fields.Date(string=u'日期')
    company_id = fields.Many2one('res.company', string=u'公司')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_id2=fields.Many2one('product.product',string=u'产品')

    @api.multi
    def action_done(self):
        report_obj = self.env['qdodoo.stock.quant.report2']
        report_ids = report_obj.search([])
        report_ids.unlink()
        sql_domain = []
        product_price_dict = {}
        ch = 0
        if not self.date or self.date >= fields.Date.today():
            # 每个公司取出一个用户
            # 根据id获取产品名字、内部编号、分类id
            product_obj = self.pool.get('product.product')
            for company_id in self.env['res.company'].search([]):
                user_ids = self.env['res.users'].search([('company_id', '=', company_id.id)])
                if user_ids:
                    user_id = user_ids[0].id
                    product_list = product_obj.search(self.env.cr, user_id,
                                                      [('type', '=', 'product'), ('company_id', '=', company_id.id)])
                    for product_brw in product_obj.browse(self.env.cr, user_id, product_list):
                        product_price_dict[product_brw.id] = product_brw.standard_price
            sql = """
                select
                    pp.name_template as product_name,
                    pp.default_code as default_code,
                    pu.name as uom,
                    sq.qty as product_qty,
                    sq.product_id as product_id
                from stock_quant sq
                    LEFT JOIN stock_location sl on sl.id = sq.location_id
                    LEFT JOIN product_product pp on pp.id = sq.product_id
                    LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                    LEFT JOIN product_uom pu on pu.id = pt.uom_id
                where sl.usage = 'internal'
            """
            # group_by_l = " group by pp.name_template,pp.default_code,sq.qty,sq.product_id,pu.name"
            ch = ch + 1
            if self.company_id:
                sql = sql + " and sq.company_id = %s"
                sql_domain.append(self.company_id.id)
                if self.product_id2:
                    sql = sql + " and sq.product_id=%s"
                    sql_domain.append(self.product_id2.id)
            else:
                if self.product_id:
                    product_ids = self.pool.get('product.product').search(self.env.cr, self.env.uid, [
                        ('name_template', '=', self.product_id.name_template)])
                    if len(product_ids) == 1:
                        sql = sql + " and sq.product_id=%s"
                        sql_domain.append(product_ids[0])
                    if len(product_ids) > 1:
                        sql = sql + " and sq.product_id in %s"
                        sql_domain.append(tuple(product_ids))
        else:
            sql = """
                select
                    pp.name_template as product_name,
                    pp.default_code as default_code,
                    pu.name as uom,
                    qpb.balance_num as product_qty,
                    qpb.balance_money as product_amount
                from qdodoo_previous_balance qpb
                    LEFT JOIN stock_location sl on sl.id = qpb.location_id
                    LEFT JOIN product_product pp on pp.id = qpb.product_id
                    LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                    LEFT JOIN product_uom pu on pu.id = pt.uom_id
                where qpb.date = '%s' and sl.usage = 'internal'
            """
            # group_by_l = " group by pp.name_template,pp.default_code,qpb.balance_num,qpb.balance_money,pu.name"
            sql_domain.append(self.date)
            ch = ch + 2
            if self.company_id:
                sql = sql + " and pt.company_id = %s"
                sql_domain.append(self.company_id.id)
                if self.product_id:
                    sql = sql + " and qpb.product_id=%s"
                    sql_domain.append(self.product_id.id)
            else:
                if self.product_id:
                    product_ids = self.pool.get('product.product').search(self.env.cr, self.env.uid, [
                        ('name_template', '=', self.product_id.name_template)])
                    if len(product_ids) == 1:
                        sql = sql + " and qpb.product_id=%s"
                        sql_domain.append(product_ids[0])
                    if len(product_ids) > 1:
                        sql = sql + " and qpb.product_id in %s"
                        sql_domain.append(tuple(product_ids))
        sql = sql % tuple(sql_domain)

        self.env.cr.execute(sql)
        res = self.env.cr.fetchall()
        # 产品名称（产品名称，编码）
        product_name = []
        product_num_dict = {}
        product_amount_dict = {}
        result_list = []
        if res:
            if ch == 1:
                for res_l in res:
                    # res_l (产品名称，编码，数量，金额)
                    k_l = res_l[0:3]
                    if k_l in product_name:
                        product_num_dict[k_l] += res_l[3]
                        product_amount_dict[k_l] += res_l[3] * product_price_dict.get(res_l[4], 0)
                    else:
                        product_num_dict[k_l] = res_l[3]
                        product_amount_dict[k_l] = res_l[3] * product_price_dict.get(res_l[4], 0)
                        product_name.append(k_l)
            elif ch == 2:
                # resl(产品名称，编码，数量，产品ID)
                for res_l in res:
                    k_l = res_l[0:3]
                    if k_l in product_name:
                        product_num_dict[k_l] += res_l[3]
                        product_amount_dict[k_l] += res_l[4]
                    else:
                        product_num_dict[k_l] = res_l[3]
                        product_amount_dict[k_l] = res_l[4]
                        product_name.append(k_l)

        else:
            raise except_orm(_(u'提示'), _(u'未查到数据'))
        for product_l in product_name:
            if product_num_dict.get(product_l, 0) == 0:
                price_unit = 0
            else:
                price_unit = product_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0)
            data = {
                'product_name': product_l[0],
                'product_default': product_l[1],
                'product_qty': product_num_dict.get(product_l, 0),
                'uom': product_l[2],
                'product_amount': product_amount_dict.get(product_l, 0),
                'price_unit': price_unit
            }
            cre_obj = report_obj.create(data)
            result_list.append(cre_obj.id)
        view_model1, tree_id = self.env['ir.model.data'].get_object_reference('qdodoo_stock_quant_date_search',
                                                                              'qdodoo_stock_quant_report2')
        view_model2, search_id = self.env['ir.model.data'].get_object_reference('qdodoo_stock_quant_date_search',
                                                                                'search_qdodoo_stock_quant_report2')
        return {
            'name': _('总库存查询'),
            'view_type': 'form',
            "view_mode": 'tree,search',
            'res_model': 'qdodoo.stock.quant.report2',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', result_list)],
            'views': [(tree_id, 'tree')],
            'view_id': [tree_id],
            'search_view_id': [search_id]
        }
