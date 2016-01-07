# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_mrp_compare_wizard(models.Model):
    _name = 'qdodoo.mrp.compare.wizard'
    _description = 'qdodoo.mrp.compare.wizard'

    start_date = fields.Date(string=u'开始时间', required=True)
    end_date = fields.Date(string=u'结束时间')
    location_id = fields.Many2one('stock.location', string=u'库位', required=True)

    @api.multi
    def action_search(self):
        sql_del1 = """delete from qdodoo_mrp_practice_compare_theory where 1=1"""
        self.env.cr.execute(sql_del1)
        sql_del2 = """delete from mrp_practice_compare_theory_line where 1=1"""
        self.env.cr.execute(sql_del2)
        if self.end_date:
            end_datetime = self.end_date + ' 23:59:59'
        else:
            end_datetime = fields.Date.today() + ' 23:59:59'
        mrp_obj = self.env['mrp.production']
        start_datetime = self.start_date + ' 00:00:01'
        location_id = self.location_id.id
        # 获取满足条件的所有生产单
        mrp_ids = mrp_obj.search([('date_planned', '>=', start_datetime), ('state', '=', 'done'),
                                  ('location_dest_id', '=', location_id), ('date_planned', '<=', end_datetime)])
        if mrp_ids:
            mrp_list = [mrp_id.id for mrp_id in mrp_ids]

            bom_list = []
            # 生产单投料数量
            sql1 = """
            select
                mp.id as id,
                mp.bom_id as bom_id,
                mp.analytic_account as analytic_account,
                sm.product_id as product_id,
                sm.product_uom_qty as product_uom_qty,
                sm.price_unit as price_unit,
                mp.product_id as product_id_mrp,
                mb.product_tmpl_id as product_tmpl_id
            from mrp_production mp
                left join stock_move sm on sm.raw_material_production_id = mp.id
                left join mrp_bom mb on mb.id = mp.bom_id
            where mp.id in %s
            """ % (tuple(mrp_list),)
            self.env.cr.execute(sql1)
            res1 = self.env.cr.fetchall()
            # 原料单价{(mp_id,bom_id,product_id):price_unit}
            product_price_dict = {}
            # 生产单投料总金额{mp_id:金额}
            mrp_amount = {}
            # 生产单辅助核算项{mp_id:analytic_account}
            mrp_account_analytic = {}
            # 每个生产单对应的bom{mp_id:bom_id}
            mrp_bom = {}
            mrp_bom_product = {}  # {bom_id:product_id}
            if res1:
                for res_1 in res1:
                    mp_id, bom_id, analytic_account, product_id, product_uom_qty, price_unit, product_id_mrp, product_tmpl_id = res_1
                    key_price = (mp_id, bom_id, product_id)
                    product_price_dict[key_price] = price_unit
                    product_unit_amount = product_uom_qty * price_unit
                    if bom_id not in bom_list:
                        bom_list.append(bom_id)
                    if (bom_id, product_tmpl_id) not in mrp_bom_product:
                        mrp_bom_product[(bom_id, product_tmpl_id)] = product_id_mrp
                    if mp_id in mrp_amount:
                        mrp_amount[mp_id] += product_unit_amount
                    else:
                        mrp_amount[mp_id] = product_unit_amount
                    if mp_id not in mrp_account_analytic:
                        mrp_account_analytic[mp_id] = analytic_account
                    if mp_id not in mrp_bom:
                        mrp_bom[mp_id] = bom_id
            # 生产单产品
            sql2 = """
            select
                mp.id as mp_id,
                sm.product_id as product_id,
                sm.product_uom_qty as product_uom_qty
            from mrp_production mp
              left join stock_move sm on sm.production_id = mp.id
            where mp.id in %s
            """ % (tuple(mrp_list),)

            self.env.cr.execute(sql2)
            res2 = self.env.cr.fetchall()
            # 生产单对应产品数量{(mrp_id,product_id):product_uom_qty)}
            mrp_product_qty = {}
            # 产品总数{mp_id:数量}
            mrp_qty = {}
            if res2:
                for res_2 in res2:
                    mp_id, product_id, product_uom_qty = res_2
                    key_m = (mp_id, product_id)
                    if key_m in mrp_product_qty:
                        mrp_product_qty[key_m] += product_uom_qty
                    else:
                        mrp_product_qty[key_m] = product_uom_qty
                    mrp_qty[mp_id] = mrp_qty.get(mp_id, 0) + product_uom_qty
            # 计算产品比例{(mp_id,product_id):比例}
            mrp_product_pro = {}
            for mrp_product_qty_l in mrp_product_qty:
                mrp_product_pro[mrp_product_qty_l] = mrp_product_qty.get(mrp_product_qty_l) / mrp_qty.get(
                    mrp_product_qty_l[0])

            # bom投料金额
            sql3 = """
                select
                mp.id as id,
                mb.id as id,
                mbl.product_id as product_id,
                mbl.product_qty as product_qty
                from mrp_production mp
                    left join mrp_bom mb on mb.id = mp.bom_id
                    left join mrp_bom_line mbl on mbl.bom_id = mb.id
                where mp.id in %s
            """ % (tuple(mrp_list),)
            self.env.cr.execute(sql3)
            res3 = self.env.cr.fetchall()
            # bom金额{(mp_id,bom_id):金额}
            bom_amount = {}
            if res3:
                for res_3 in res3:
                    mp_id, mb_id, product_id, product_qty = res_3
                    # 取产品单价key
                    price_key = (mp_id, mb_id, product_id)
                    bom_amount[(mp_id, mb_id)] = bom_amount.get((mp_id, mb_id),
                                                                0) + product_qty * product_price_dict.get(
                        price_key, 0)

            bom_ids = self.env['mrp.bom'].browse(bom_list)
            # 计算bom产品数量
            bom_product_num = {}  # {(bom_id,product_id):数量}
            bom_num = {}  # {bom_id:数量}
            for bom_id in bom_ids:
                bm_id = bom_id.id
                num = bom_id.product_qty
                product_tmpl_id = bom_id.product_tmpl_id.id
                product_id = mrp_bom_product.get((bm_id, product_tmpl_id))
                key_m = (bm_id, product_id)
                bom_num[bm_id] = bom_num.get(bm_id, 0) + num
                bom_product_num[key_m] = bom_product_num.get(key_m, 0) + bom_id.product_qty
                if bom_id.sub_products:
                    for sub_product in bom_id.sub_products:
                        num = sub_product.product_qty
                        bom_num[bm_id] = bom_num.get(bm_id, 0) + num
                        product_id = sub_product.product_id.id
                        key_m2 = (bom_id.id, product_id)
                        bom_product_num[key_m2] = bom_product_num.get(key_m2, 0) + num
            # 计算Bom产品比例
            bom_product_pro = {}  # {(bom_id,product_id):比例}
            for bom_product_num_l in bom_product_num:
                bom_product_pro[bom_product_num_l] = bom_product_num.get(bom_product_num_l) / bom_num.get(
                    bom_product_num_l[0])

            product_info = {}  # {product_id:[{}]}
            product_data = {}  # {product_id:{}}
            for mpq in mrp_product_qty:
                mp_id, product_id = mpq
                bm_id = mrp_bom.get(mp_id)  # 生产单对应的bom_id
                product_pro = mrp_product_pro.get(mpq)  # 实际比例
                product_pro2 = bom_product_pro.get((bm_id, product_id))  # 理论比例
                mrp_number = mrp_qty.get(mp_id)  # 生产单数量
                bom_number = bom_num.get(bm_id)  # bom数量
                product_number = mrp_number * product_pro  # 实际数量
                mrp_a = mrp_amount.get(mp_id)  # 实际生产单金额
                bom_a = bom_amount.get((mp_id, bm_id))  # bom金额
                product_amount = mrp_a * product_pro  # 实际金额
                product_amount2 = mrp_number / bom_number * bom_a  # 理论金额
                product_number2 = mrp_a / bom_a * bom_number * product_pro2  # 计划数量
                product_price = product_amount / product_number  # 实际单价
                product_price2 = product_amount2 / product_number2  # 理论单价
                amount_compare = product_amount - product_amount2  # 节约金额
                unit_compare = -product_price - product_price2  # 单份节约金额
                if product_id not in product_info:
                    p_list = []
                    data = {
                        'mp_id': mp_id,  # 生产单
                        'product_id': product_id,  # 产品
                        'product_number': product_number,  # 实际数量
                        'product_number2': product_number2,  # 计划数量
                        'product_amount': product_amount,  # 实际金额
                        'product_amount2': product_amount2,  # 理论金额
                        'product_price': product_price,  # 实际单价
                        'product_price2': product_price2,  # 理论单价
                        'amount_compare': amount_compare,  # 节约金额
                        'unit_compare': unit_compare,  # 单份节约金额
                        'analytic_account': mrp_account_analytic.get(mp_id)
                    }
                    p_list.append(data)
                    product_info[product_id] = p_list
                else:
                    data = {
                        'mp_id': mp_id,  # 生产单
                        'product_id': product_id,  # 产品
                        'product_number': product_number,  # 实际数量
                        'product_number2': product_number2,  # 计划数量
                        'product_amount': product_amount,  # 实际金额
                        'product_amount2': product_amount2,  # 理论金额
                        'product_price': product_price,  # 实际单价
                        'product_price2': product_price2,  # 理论单价
                        'amount_compare': amount_compare,  # 节约金额
                        'unit_compare': unit_compare,  # 单份节约金额
                        'analytic_account': mrp_account_analytic.get(mp_id)
                    }
                    product_info[product_id].append(data)
                if product_id not in product_data:
                    p_dict = {
                        'product_number': product_number,  # 实际数量
                        'product_number2': product_number2,  # 计划数量
                        'product_amount': product_amount,  # 实际金额
                        'product_amount2': product_amount2,  # 理论金额
                        'product_price': product_price,  # 实际单价
                        'product_price2': product_price2,  # 理论单价
                        'amount_compare': amount_compare,  # 节约金额
                        'unit_compare': unit_compare,  # 单份节约金额
                        # 'location_id': self.location_id.id
                    }
                    product_data[product_id] = p_dict
                else:
                    p_dict = product_data[product_id]
                    p_dict['product_number'] = p_dict.get('product_number') + product_number
                    p_dict['product_number2'] = p_dict.get('product_number2') + product_number2
                    p_dict['product_amount'] = p_dict.get('product_amount') + product_amount
                    p_dict['product_amount2'] = p_dict.get('product_amount2') + product_amount2
                    p_dict['product_price'] = (p_dict.get('product_price') + product_price) / 2
                    p_dict['product_price2'] = (p_dict.get('product_price2') + product_price2) / 2
                    p_dict['amount_compare'] = p_dict.get('amount_compare') + amount_compare
                    p_dict['unit_compare'] = (p_dict.get('unit_compare') + unit_compare) / 2
            result_list = []
            for product_l in product_data:
                product_number = product_data.get(product_l).get('product_number')
                product_number2 = product_data.get(product_l).get('product_number2')
                product_amount = product_data.get(product_l).get('product_amount')
                product_amount2 = product_data.get(product_l).get('product_amount2')
                product_price = product_data.get(product_l).get('product_price')
                product_price2 = product_data.get(product_l).get('product_price2')
                amount_compare = product_amount - product_amount2
                unit_compare = product_price - product_price2
                rate_l = (product_amount - product_amount2) / product_amount2
                rate_l_new = str("%.4f" % (rate_l * 100)) + "%"
                sql_into = """
                insert into qdodoo_mrp_practice_compare_theory (location_id,product_id,product_number,product_number2,product_amount,product_amount2,product_price,product_price2,amount_compare,unit_compare,rate) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'%s') returning id
                """ % (
                    self.location_id.id, product_l, product_number, product_number2, product_amount, product_amount2,
                    product_price,
                    product_price2,
                    amount_compare, unit_compare, rate_l_new)
                self.env.cr.execute(sql_into)
                compare_id = self.env.cr.fetchall()[0][0]
                product_list = product_info.get(product_l, [])
                for p_l in product_list:
                    mp_id = p_l.get('mp_id')
                    product_id = p_l.get('product_id')
                    product_number = p_l.get('product_number')
                    product_number2 = p_l.get('product_number2')
                    product_amount = p_l.get('product_amount')
                    product_amount2 = p_l.get('product_amount2')
                    product_price = p_l.get('product_price')
                    product_price2 = p_l.get('product_price2')
                    analytic_account = p_l.get('analytic_account')
                    amount_compare = product_amount - product_amount2
                    unit_compare = product_price - product_price2
                    rate_l = (product_amount - product_amount2) / product_amount2
                    rate2 = str("%.4f" % (rate_l * 100)) + "%"
                    sql_into2 = """
                    insert into mrp_practice_compare_theory_line (analytic_account,compare_id,mp_id,product_id,product_number,product_number2,product_amount,product_amount2,product_price,product_price2,amount_compare,unit_compare,rate) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'%s') returning id
                    """ % (analytic_account, compare_id, mp_id,
                           product_id, product_number, product_number2, product_amount, product_amount2, product_price,
                           product_price2,
                           amount_compare, unit_compare, rate2)
                    self.env.cr.execute(sql_into2)
                result_list.append(compare_id)
            model_obj = self.env['ir.model.data']
            tree_model, tree_id = model_obj.get_object_reference('qdodoo_mrp_practice_compare_theory',
                                                                 'qdodoo_compare_cost_report_tree')
            form_model, form_id = model_obj.get_object_reference('qdodoo_mrp_practice_compare_theory',
                                                                 'qdodoo_compare_cost_report_form')
            return {
                'name': (u'报表'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'qdodoo.mrp.practice.compare.theory',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', result_list)],
                'views': [(tree_id, 'tree'), (form_id, 'form')],
                'view_id': [tree_id]
            }
        else:
            raise except_orm(_(u'提示'), _(u'未查询到数据'))








            # mrp_list = []
            # # 生产单对应的bom对象字典{mp_id:bom对象}
            # mrp_bom = {}
            # # 循环所有的生产单
            # # 每个生产单对应的产品所占的比例{mrp_id:{product_id:比例}}
            # mrp_product_proportion = {}
            # # 每个原料的单价{mrp_id:{product_id:单价}}
            # mrp_raw_material = {}
            # # 生产单原料消耗总金额{mrp_id:金额}
            # mrp_amount = {}
            # # 生产单生产的产品数量{mrp_id:数量}
            # mrp_product_num = {}
            # for mrp_id in mrp_ids:
            #     mp_id = mrp_id.id
            #     mrp_list.append(mp_id)
            #     bom_id = mrp_id.bom_id
            #     mrp_bom[mp_id] = bom_id
            #     mrp_product_proportion[mp_id] = {}
            #     # 产品数量{product_id:数量}
            #     product_proportion = {}
            #     total_num = 0
            #     if mrp_id.move_created_ids2:
            #         for move_created_id in mrp_id.move_created_ids2:
            #             total_num += move_created_id.product_uom_qty
            #             product_id = move_created_id.product_id.id
            #             if product_id in product_proportion:
            #                 product_proportion[product_id] += move_created_id.product_uom_qty
            #             else:
            #                 product_proportion[product_id] = move_created_id.product_uom_qty
            #         mrp_product_num[mp_id] = product_proportion
            #         for product_proportion_l in product_proportion:
            #             mrp_product_proportion[mp_id][product_proportion_l] = product_proportion.get(product_proportion_l,
            #                                                                                          0) / total_num
            #     if mrp_id.move_lines2:
            #         # 原料总价
            #         move_amount = 0
            #         # 原料单价{product_id:单价}
            #         move_product_price = {}
            #         # 每条明细的总价{product_id:总价}
            #         line_product_amount = {}
            #         # 每条明细的数量{product_id:数量}
            #         line_product_num = {}
            #         for move_line in mrp_id.move_lines2:
            #             product_id = move_line.product_id.id
            #             product_qty = move_line.product_uom_qty
            #             product_price = move_line.price_unit
            #             line_amount = product_qty * product_price
            #             move_amount += line_amount
            #             if product_id in line_product_amount:
            #                 line_product_amount[product_id] += line_amount
            #             else:
            #                 line_product_amount[product_id] = line_amount
            #             if product_id in line_product_num:
            #                 line_product_num[product_id] += product_qty
            #             else:
            #                 line_product_num[product_id] = product_qty
            #             line_product_amount[product_id] = line_amount
            #         mrp_amount[mp_id] = move_amount
            #         # 求原料单价
            #         for line_product_amount_l in line_product_amount:
            #             move_product_price[line_product_amount_l] = line_product_amount.get(line_product_amount_l,
            #                                                                                 0) / line_product_num.get(
            #                 line_product_amount_l, 0)
            #         mrp_raw_material[mp_id] = move_product_price
            # # 循环bom
            # # 产品比例{bom_id:{product_id:比例}}
            # bom_product_proportion = {}
            # # bom原料消耗金额{bom_id:金额}
            # bom_amount = {}
            # # bom对象的产品数量{bom_id:总数}
            # bom_product_num = {}
            # # bom对象列表
            # bom_list = []
            # for mp_id in mrp_list:
            #     bom_id = mrp_bom.get(mp_id, False)
            #     if bom_id and bom_id not in bom_list:
            #         bm_id = bom_id.id
            #         total_num = bom_id.product_qty
            #         # 产品数量
            #         product_proportion = {}
            #         bom_product_proportion[bm_id] = {}
            #         product_proportion[bom_id.product_id.id] = total_num
            #         if bom_id.sub_products:
            #             for sub_product in bom_id.sub_products:
            #                 total_num += sub_product.product_qty
            #                 product_id = sub_product.product_id.id
            #                 if product_id in product_proportion:
            #                     product_proportion[product_id] += sub_product.product_qty
            #                 else:
            #                     product_proportion[product_id] = sub_product.product_qty
            #             for product_proportion_l in product_proportion:
            #                 bom_product_proportion[bm_id][product_proportion_l] = product_proportion.get(
            #                     product_proportion_l,
            #                     0) / total_num
            #         bom_product_num[bm_id] = total_num
            #     bom_list.append(bom_id)
            #     # 明细金额
            #     b_amount = 0
            #     if bom_id.bom_line_ids:
            #         for bom_line in bom_id.bom_line_ids:
            #             product_id = bom_line.product_id.id
            #             b_amount += bom_line.product_qty * mrp_raw_material.get(mp_id, {}).get(product_id, 0)
            #         bom_amount[bom_id.id] = b_amount
            #
            # # {product_id:{mrp_id:[]}}
            # product_dict = {}
            # # 产品汇总
            # mrp_amount_total = {}  # 实际金额汇总
            # mrp_product_num_total = {}  # 实际数量汇总
            # product_price_total = {}  # 实际单价汇总
            # bom_prod_num_total = {}  # 理论数量汇总
            # bom_amu_total = {}  # 理论金额汇总
            # product_price2_total = {}  # 理论单价汇总
            # amount_compare_total = {}  # 节约金额汇总
            # unit_compare_total = {}  # 单份节约金额汇总
            # for mrp_l in mrp_ids:
            #     mrp_id = mrp_l.id
            #     bom_id = mrp_l.bom_id.id
            #     # 成品总数
            #     mrp_num = mrp_product_num.get(mrp_id, 0)
            #     # 每个生产单的实际金额
            #     mrp_amount1 = mrp_raw_material.get(mrp_id, 0)
            #     # 每个生产单的理论金额
            #     mrp_amount2 = bom_amount.get(bom_id, 0)
            #     bom_pro_num = mrp_amount1 / mrp_amount2 * bom_product_num.get(bom_id, 0)  # 理论总数量
            #     # mrp_product_dict={}
            #     bom_product_pro = bom_product_proportion.get(bom_id, {})
            #     product_dict1 = mrp_product_proportion.get(mrp_id, {})
            #     if product_dict1:
            #         for product_l1 in product_dict1:
            #             product_id = product_l1,  # 产品
            #             product_pro = product_dict1.get(product_l1)  # 实际比例
            #             mrp_amount = mrp_amount1 * product_pro  # 实际金额
            #             mrp_product_num = mrp_num * product_pro  # 实际数量
            #             product_price = mrp_amount / mrp_product_num  # 实际单价
            #             product_pro2 = bom_product_pro.get(product_l1)  # 理论比例
            #             bom_prod_num = bom_pro_num * product_pro2  # 理论数量
            #             bom_amu = mrp_amount2 * product_pro2  # 理论金额
            #             product_price2 = bom_amu / bom_prod_num  # 理论单价
            #             amount_compare = mrp_amount - bom_amu  # 节约金额
            #             unit_compare = product_price - product_price2  # 单份节约金额
            #             ##########汇总
            #             mrp_amount_total[product_l1] = mrp_amount_total.get(product_l1, 0) + mrp_amount
            #             mrp_product_num_total[product_l1] = mrp_product_num_total.get(product_l1, 0) + mrp_product_num
            #             if product_l1 in product_price_total:
            #                 product_price_total[product_l1] = product_price
            #             else:
            #                 product_price_total[product_l1] = (product_price + product_price_total.get(product_l1, 0)) / 2
            #             bom_prod_num_total[product_l1] = bom_prod_num_total.get(product_l1, 0) + bom_prod_num
            #             bom_amu_total[product_l1] = bom_amu_total.get(product_l1, 0) + bom_amu
            #             if product_l1 in product_price2_total:
            #                 product_price2_total[product_l1] = product_price2
            #             else:
            #                 product_price2_total[product_l1] = (
            #                                                    product_price2 + product_price2_total.get(product_l1, 0)) / 2
            #             amount_compare_total[product_l1] = amount_compare_total.get(product_l1, 0) + amount_compare
            #             if product_l1 in unit_compare_total:
            #                 unit_compare_total[product_l1] = unit_compare
            #             else:
            #                 unit_compare_total[product_l1] = (unit_compare_total.get(product_l1, 0) + unit_compare) / 2
            #             if product_dict1 in product_dict:
            #                 data = {
            #                     'product_id': product_id,  # 产品
            #                     'mrp_id': mrp_id,  # 生产单
            #                     'mrp_product_num': mrp_product_num,
            #                     'mrp_amount': mrp_amount,
            #                     'product_price': product_price,
            #                     'bom_amu': bom_amu,
            #                     'bom_prod_num': bom_prod_num,
            #                     'product_price2': product_price2,
            #                     'amount_compare': amount_compare,
            #                     'unit_compare': unit_compare
            #                 }
            #                 product_dict[product_l1].append(data)
            #             else:
            #                 product_dict[product_l1] = []
            #                 data = {
            #                     'product_id': product_id,  # 产品
            #                     'mrp_id': mrp_id,  # 生产单
            #                     'mrp_product_num': mrp_product_num,
            #                     'mrp_amount': mrp_amount,
            #                     'product_price': product_price,
            #                     'bom_amu': bom_amu,
            #                     'bom_prod_num': bom_prod_num,
            #                     'product_price2': product_price2,
            #                     'amount_compare': amount_compare,
            #                     'unit_compare': unit_compare
            #                 }
            #                 product_dict[product_l1].append(data)
