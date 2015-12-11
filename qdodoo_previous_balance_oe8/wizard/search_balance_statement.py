# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import except_orm


class qdodoo_search_balance_statement(models.Model):
    _name = "qdodoo.search.balance.statement"
    _description = "search.balance.statement"

    def start_date(self):
        """
            本月初
        """

        now_date = fields.Date.today()
        return now_date

    start_date = fields.Date(string=u'开始日期', required=True, default=start_date)
    end_date = fields.Date(string=u'结束日期')
    location_id = fields.Many2one('stock.location', string=u'库位')
    product_id = fields.Many2one('product.product', string=u'产品')
    company_id = fields.Many2one('res.company', string=u'公司')

    @api.multi
    def balance_statement_open_window(self):
        unlink_ids = self.env["qdodoo.result.balance.statement"].search([])
        unlink_ids.unlink()
        mod_obj = self.env['ir.model.data']
        result_list = []
        if self.end_date and self.start_date > self.end_date:
            raise except_orm(_(u'对不起'), _(u'开始日期不能大于结束日期！'))
        # 获取所有库位id
        location_list = []
        location_name_dict = {}
        if self.company_id:
            location_ids = self.env['stock.location'].search([('company_id', '=', self.company_id.id)])
            for location_id in location_ids:
                location_name_dict[location_id.id] = location_id.complete_name.split('/', 1)[
                    1] if location_id.location_id else location_id.complete_name
                location_list.append(location_id.id)
        if self.location_id:
            location_list.append(self.location_id.id)
            location_name_dict[self.location_id.id] = self.location_id.complete_name.split('/', 1)[
                1] if self.location_id.location_id else self.location_id.complete_name
        # 获取查询条件中的开始时间和结束时间
        balance_obj = self.env["qdodoo.previous.balance"]
        now_date = fields.Date.today()
        start_date = self.start_date + " 00:00:01"
        read_dict = balance_obj.browse(1)
        if start_date <= read_dict.date:
            date_start_limit = (
                datetime.datetime.strptime(read_dict.date, DEFAULT_SERVER_DATE_FORMAT) - datetime.timedelta(
                    days=-1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            raise except_orm(_(u'警告'), _(u'开始时间超出查询范围，开始时间最早只能为%s') % (date_start_limit))

        end_date = (self.end_date if self.end_date else now_date) + " 23:59:59"

        # 每个公司取出一个用户
        # 根据id获取产品名字、内部编号、分类id
        product_obj = self.pool.get('product.product')
        dict_product = {}
        dict_product_name = {}
        dict_category_id = {}
        product_list_l = []
        product_price_dict = {}
        product_company_dict = {}
        for company_id in self.env['res.company'].search([]):
            user_ids = self.env['res.users'].search([('company_id', '=', company_id.id)])
            if user_ids:
                user_id = user_ids[0].id
                product_list = product_obj.search(self.env.cr, user_id,
                                                  [('type', '=', 'product'), ('company_id', '=', company_id.id)])
                for product_brw in product_obj.browse(self.env.cr, user_id, product_list):
                    product_price_dict[product_brw.id] = product_brw.standard_price
                    dict_product[product_brw.id] = product_brw.name
                    dict_product_name[product_brw.id] = product_brw.default_code
                    dict_category_id[product_brw.id] = product_brw.categ_id.id
                    product_list_l.append(product_brw.id)
                    product_company_dict[product_brw.id] = company_id.id

        product_dict = {}  # 本期结余数量
        product_amount_dict = {}  # 本期结余金额
        quant_obj = self.env['stock.quant']
        quant_ids = quant_obj.search([('location_id', 'in', location_list)])
        if quant_ids:
            for quant_id in quant_ids:
                qant_key = (quant_id.location_id.id, quant_id.product_id.id)
                if qant_key in product_dict:
                    product_dict[qant_key] += quant_id.qty
                    product_amount_dict[qant_key] += quant_id.qty * product_price_dict.get(quant_id.product_id.id, 0)
                else:
                    product_dict[qant_key] = quant_id.qty
                    product_amount_dict[qant_key] = quant_id.qty * product_price_dict.get(quant_id.product_id.id, 0)
        # 前期结余
        balance_num_dict = {}
        balance_mount_dict = {}
        # 获取昨天的日期
        yesterday = (datetime.datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - datetime.timedelta(
            days=1)).strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        balance_ids = balance_obj.search([('date', '=', yesterday), ('product_id', 'in', product_list_l),
                                          ('location_id', 'in', location_list)])
        for balance_brw in balance_ids:
            key_balance = (balance_brw.location_id.id, balance_brw.product_id.id)
            balance_num_dict[key_balance] = balance_brw.balance_num
            balance_mount_dict[key_balance] = balance_brw.balance_money
        if end_date:
            balance_ids_new = balance_obj.search([('date', '=', end_date), ('location_id', 'in', location_list),
                                                  ('product_id', 'in', product_list_l)])
            if balance_ids_new:
                product_dict = {}
                for balance_brw_new in balance_ids_new:
                    key_balance_new = (balance_brw_new.location_id.id, balance_brw_new.product_id.id)
                    product_dict[key_balance_new] = balance_brw_new.balance_num
                    product_amount_dict[key_balance_new] = balance_brw_new.balance_money


        # 入库数量
        num_dict = {}
        move_in_mount = {}
        move_in_list = []
        move_obj = self.env["stock.move"]

        move_ids = move_obj.search([('product_id', 'in', product_list_l), ('state', '=', 'done'),
                                    ('date', '>=', start_date), ('date', '<=', end_date),
                                    ('location_dest_id', 'in', location_list)])
        for move_brw in move_ids:
            key_in = (move_brw.location_dest_id.id, move_brw.product_id.id)
            if key_in in move_in_list:
                num_dict[key_in] += move_brw.product_uom_qty
                move_in_mount[key_in] += move_brw.product_uom_qty * move_brw.tfs_price_unit
            else:
                num_dict[key_in] = move_brw.product_uom_qty
                move_in_mount[key_in] = move_brw.product_uom_qty * move_brw.tfs_price_unit
                move_in_list.append(key_in)
        # 查询产品的出库数量
        move_out_dict = {}
        move_out_mount = {}
        move_out_list = []
        move_out_ids = move_obj.search([('product_id', 'in', product_list_l), ('state', '=', 'done'),
                                        ('date', '>=', start_date), ('date', '<=', end_date),
                                        ('location_id', 'in', location_list)])
        for move_out_id in move_out_ids:
            key_out = (move_out_id.location_id.id, move_out_id.product_id.id)
            if key_out in move_out_list:
                move_out_dict[key_out] += move_out_id.product_uom_qty
                move_out_mount[key_out] += move_out_id.product_uom_qty * move_out_id.tfs_price_unit
            else:
                move_out_dict[key_out] = move_out_id.product_uom_qty
                move_out_mount[key_out] = move_out_id.product_uom_qty * move_out_id.tfs_price_unit
                move_out_list.append(key_out)

        product_list_new = list(set(move_in_list + move_out_list + product_dict.keys() + product_amount_dict.keys()))
        # 循环所有查询出来的数据
        for product_l in product_list_new:
            result = {
                'name': location_name_dict.get(product_l[0], ''),  # 库位名称
                'product_name': dict_product.get(product_l[1], ''),  # 产品名称
                'product_id': product_l[1],
                'pre_balance': balance_num_dict.get(product_l, 0.0),  # 前期结余数量
                'pre_balance_amount': balance_mount_dict.get(product_l, 0),  # 前期结余金额
                'storage_quantity_amount': move_in_mount.get(product_l, 0),  # 入库金额
                'storage_quantity_period': num_dict.get(product_l, 0.0),  # 本期入库数量
                'number_of_library': move_out_dict.get(product_l, 0.0),  # 本期出库数量
                'number_of_library_amount': move_out_mount.get(product_l, 0),  # 出库金额
                'current_balance': product_dict.get(product_l, 0.0),  # 本期结余数量
                'current_balance_amount': product_amount_dict.get(product_l, 0),  # 本期结余金额
                'company_id': product_company_dict.get(product_l[1], False)
            }
            cre_obj = self.env["qdodoo.result.balance.statement"].create(result)
            result_list.append(cre_obj.id)

        if self.location_id:
            view_model, view_id = mod_obj.get_object_reference('qdodoo_previous_balance_oe8',
                                                               'view_result_balance_statement_tree')
            return {
                'name': _('库存结余报表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.result.balance.statement',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', result_list)],
                'views': [(view_id, 'tree')],
                'view_id': [view_id],
            }
        if self.company_id:
            view_model, view_id = mod_obj.get_object_reference('qdodoo_previous_balance_oe8',
                                                               'view_result_balance_statement_tree2')
            return {
                'name': _('库存结余报表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.result.balance.statement',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', result_list)],
                'views': [(view_id, 'tree')],
                'view_id': [view_id],
            }


class qdodoo_result_balance_statement(models.Model):
    _name = 'qdodoo.result.balance.statement'
    _description = 'qdodoo.result.balance.statement'
    product_name = fields.Char(u'产品')
    product_id = fields.Many2one('product.product', u'产品')
    name = fields.Char(u'库位')
    pre_balance = fields.Float(string=u'前期结余数量')
    pre_balance_amount = fields.Float(string=u'前期结余金额', digits=(16, 4))
    storage_quantity_period = fields.Float(string=u'本期入库数量')
    storage_quantity_amount = fields.Float(string=u'本期入库金额', digits=(16, 4))
    number_of_library = fields.Float(string=u'本期出库数量')
    number_of_library_amount = fields.Float(string=u'本期出库金额', digits=(16, 4))
    current_balance = fields.Float(string=u'本期结余数量')
    current_balance_amount = fields.Float(string=u'本期结余金额', digits=(16, 4))
    company_id = fields.Many2one('res.company', string=u'公司')
