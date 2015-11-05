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
    line_ids = fields.One2many('compare.product.cost.line', 'product_cost_id', string=u'明细')


class qdodoo_compare_product_cost_report_line(models.Model):
    _name = 'compare.product.cost.line'

    mo_name = fields.Char(string=u'生产单号')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_qty = fields.Float(string=u'计划数量')
    product_l_num=fields.Float(string=u'实际数量')
    actual_amount = fields.Float(digits=(16, 4), string=u'实际金额')
    actual_price = fields.Float(digits=(16, 4), string=u'实际单价')
    theoretical_amount = fields.Float(digits=(16, 4), string=u'理论金额')
    theoretical_price = fields.Float(digits=(16, 4), string=u'理论单价')
    save_amount = fields.Float(digits=(16, 4), string=u'节约金额')
    price_save = fields.Float(digits=(16, 4), string=u'单份节约金额')
    product_cost_id = fields.Many2one('compare.product.cost', string=u'对比表', ondelete='cascade')


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

            actual_amount_list = []  # 生产单实际原料
            actual_amount_dict = {}  # 生产单实际成本
            product_price_dict = {}  # 生产单实际投料原料单价
            theoretical_amount_list = []  # 生产单理论原料
            theoretical_amount_dict = {}  # 生产单理论成本
            product_num_dict = {}  # 生产单成品数量
            key_list = []  # 最终key值
            product_total_a = {}  # 最终实际成本
            product_total_t = {}  # 最终理论成本
            line_dict = {}  # 明细
            end_num_dict = {}  # 成品数量
            result_list = []
            if mrp_ids:
                for mrp_id in mrp_ids:
                    price_amount_dict = {}  # 实际原料金额
                    product_price_list = []  # 实际原料
                    sm_num_dict = {}
                    if mrp_id.move_created_ids2:
                        for move_l in mrp_id.move_created_ids2:
                            if move_l.state != 'cancel':
                                product_num_dict[
                                    (mrp_id.id, mrp_id.name, mrp_id.product_id.id,
                                     mrp_id.analytic_account.id)] = product_num_dict.get(
                                    (mrp_id.id, mrp_id.name, mrp_id.product_id.id,
                                     mrp_id.analytic_account.id), 0) + move_l.product_uom_qty
                    sql = """
                        select
                            mp.id,
                            mp.name,
                            mp.product_id,
                            mp.analytic_account,
                            sm.product_id as product_id_y,
                            sm.price_unit as price_unit,
                            sm.product_uom_qty as product_uom_qty
                        from mrp_production mp
                            LEFT JOIN stock_move sm ON sm.raw_material_production_id = mp.id
                        where mp.id=%s and mp.state='done' and sm.product_uom_qty>0 and mp.date_planned >= '%s' and mp.date_planned <= '%s'
                        group by
                            mp.id,mp.name,mp.product_id,mp.analytic_account,sm.product_id,mp.state,mp.date_planned,sm.price_unit,sm.product_uom_qty,sm.raw_material_production_id
                        """ % (mrp_id.id, datetime_start, datetime_end)

                    self.env.cr.execute(sql)
                    result = self.env.cr.fetchall()

                    if result:
                        for i in result:
                            mp_id, mp_name, mp_product_id, mp_analytic, sm_product_id, sm_price_unit, sm_product_qty = i
                            if (mp_id, mp_name, mp_product_id, mp_analytic) in actual_amount_list:
                                actual_amount_dict[
                                    (mp_id, mp_name, mp_product_id, mp_analytic)] += sm_price_unit * sm_product_qty
                            else:
                                actual_amount_dict[
                                    (mp_id, mp_name, mp_product_id, mp_analytic)] = sm_price_unit * sm_product_qty
                                actual_amount_list.append((mp_id, mp_name, mp_product_id, mp_analytic))
                            if (mp_id, sm_product_id) in product_price_list:
                                price_amount_dict[(mp_id, sm_product_id)] += sm_price_unit * sm_product_qty
                                sm_num_dict[(mp_id, sm_product_id)] += sm_product_qty
                            else:
                                price_amount_dict[(mp_id, sm_product_id)] = sm_price_unit * sm_product_qty
                                sm_num_dict[(mp_id, sm_product_id)] = sm_product_qty
                                product_price_list.append((mp_id, sm_product_id))

                        for unit_l in product_price_list:
                            product_price_dict[unit_l] = price_amount_dict.get(unit_l, 0) / sm_num_dict.get(unit_l, 0)
                    sql2 = """
                        select
                        mp2.id,
                        mp2.name,
                        mp2.product_id,
                        mp2.analytic_account,
                        mppl.product_id,
                        mppl.product_qty
                        from  mrp_production mp2
                        LEFT JOIN mrp_production_product_line mppl ON mppl.production_id=mp2.id
                        WHERE mp2.id=%s and mp2.date_planned >= '%s' and mp2.date_planned <= '%s'
                        group by mp2.id,mp2.name,mp2.product_id,mp2.analytic_account,mppl.product_id,mppl.product_qty,mp2.date_planned
                    """ % (mrp_id.id, datetime_start, datetime_end)
                    self.env.cr.execute(sql2)
                    result2 = self.env.cr.fetchall()
                    if result2:
                        for j in result2:
                            mp_id, mp_name, mp_product_id, mp_analytic, mppl_product_id, mppl_product_qty = j
                            if (mp_id, mp_name, mp_product_id, mp_analytic) in theoretical_amount_list:
                                theoretical_amount_dict[
                                    (mp_id, mp_name, mp_product_id,
                                     mp_analytic)] += mppl_product_qty * product_price_dict.get(
                                    (mp_id, mppl_product_id), 0)
                            else:
                                theoretical_amount_dict[
                                    (mp_id, mp_name, mp_product_id,
                                     mp_analytic)] = mppl_product_qty * product_price_dict.get(
                                    (mp_id, mppl_product_id), 0)
                                theoretical_amount_list.append((mp_id, mp_name, mp_product_id, mp_analytic))
                if len(list(set(actual_amount_list + theoretical_amount_list))):
                    for product_l in list(set(actual_amount_list + theoretical_amount_list)):
                        product_key = product_l[2:]
                        sss = actual_amount_dict.get(product_l, 0) - theoretical_amount_dict.get(product_l, 0)
                        if product_key in key_list:
                            product_total_a[product_key] += actual_amount_dict.get(product_l, 0)
                            product_total_t[product_key] += theoretical_amount_dict.get(product_l, 0)
                            end_num_dict[product_key] += product_num_dict.get(product_l, 0)
                            line_dict[product_key] += [(
                                product_l[1], product_l[2], actual_amount_dict.get(product_l, 0),
                                actual_amount_dict.get(product_l, 0) / product_num_dict.get(
                                    product_l, 0), theoretical_amount_dict.get(product_l, 0),
                                theoretical_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0),
                                sss, (
                                    actual_amount_dict.get(product_l, 0) - theoretical_amount_dict.get(product_l,
                                                                                                       0)) / product_num_dict.get(
                                    product_l, 0))]
                        else:
                            product_total_a[product_key] = actual_amount_dict.get(product_l, 0)
                            product_total_t[product_key] = theoretical_amount_dict.get(product_l, 0)
                            end_num_dict[product_key] = product_num_dict.get(product_l, 0)
                            ss = actual_amount_dict.get(product_l, 0) - theoretical_amount_dict.get(product_l, 0)
                            line_dict[product_key] = [(
                                product_l[1], product_l[2], actual_amount_dict.get(product_l, 0),
                                actual_amount_dict.get(product_l, 0) / product_num_dict.get(
                                    product_l, 0), theoretical_amount_dict.get(product_l, 0),
                                theoretical_amount_dict.get(product_l, 0) / product_num_dict.get(product_l, 0),
                                sss, (
                                    actual_amount_dict.get(product_l, 0) - theoretical_amount_dict.get(product_l,
                                                                                                       0)) / product_num_dict.get(
                                    product_l, 0))]
                            key_list.append(product_key)

                if key_list:
                    for key_l in key_list:
                        if product_total_t.get(key_l, 0) == 0:
                            rate_l = "0%"
                        else:
                            rate_l = str("%.4f" % (
                                (product_total_a.get(key_l, 0) - product_total_t.get(key_l, 0)) / product_total_t.get(
                                    key_l,
                                    0) * 100)) + "%"

                        data = {
                            'product_id': key_l[0],
                            'product_qty': end_num_dict.get(key_l, 0),
                            'location_id': self.location_id.id,
                            'assistant_id': key_l[-1],
                            'actual_amount': product_total_a.get(key_l, 0),
                            'actual_price': product_total_a.get(key_l, 0) / end_num_dict.get(key_l, 0),
                            'theoretical_amount': product_total_t.get(key_l, 0),
                            'theoretical_price': product_total_t.get(key_l, 0) / end_num_dict.get(key_l, 0),
                            'save_amount': product_total_a.get(key_l, 0) - product_total_t.get(key_l, 0),
                            'price_save': (product_total_a.get(key_l, 0) - product_total_t.get(key_l,
                                                                                               0)) / end_num_dict.get(
                                key_l, 0),
                            'amount_difference_rate': rate_l
                        }
                        cre_obj = self.env['compare.product.cost'].create(data)
                        result_list.append(cre_obj.id)
                        if line_dict.get(key_l, False):
                            for p in line_dict[key_l]:
                                product_l_s = 0
                                mp_obj = self.env['mrp.production'].search([('name', '=', p[0])])
                                for li in mp_obj.move_created_ids2:
                                    if li.state != 'cancel':
                                        product_l_s += li.product_uom_qty

                                mo_name_line = p[0]
                                product_id_line = p[1]
                                product_qty = mp_obj.product_qty
                                product_l_num = product_l_s
                                actual_amount_line = p[2]
                                actual_price_line = p[3]
                                theoretical_amount_line = p[4]
                                theoretical_price_line = p[5]
                                save_amount_line = p[6]
                                price_save_line = p[-1]
                                sql_line = """
                                insert into compare_product_cost_line (product_qty,product_l_num,mo_name,product_id,actual_amount,actual_price,theoretical_amount,theoretical_price,save_amount,price_save,product_cost_id) VALUES (%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s)
                                """ % (
                                    product_qty, product_l_num,mo_name_line, product_id_line, actual_amount_line, actual_price_line,
                                    theoretical_amount_line, theoretical_price_line, save_amount_line,
                                    price_save_line, cre_obj.id)
                                self.env.cr.execute(sql_line)

                view_model, view_id = self.env['ir.model.data'].get_object_reference(
                    'qdodoo_comparison_cost_product_report', 'qdodoo_compare_cost_report_tree')
                view_model2, view_id2 = self.env['ir.model.data'].get_object_reference(
                    'qdodoo_comparison_cost_product_report', 'qdodoo_compare_cost_report_form')
                return {
                    'name': (u'产品标准原料成本与实际成本对比汇总表'),
                    'view_type': 'form',
                    "view_mode": 'tree',
                    'res_model': 'compare.product.cost',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', result_list)],
                    'views': [(view_id, 'tree'), (view_id2, 'form')],
                    'view_id': [view_id],
                }
