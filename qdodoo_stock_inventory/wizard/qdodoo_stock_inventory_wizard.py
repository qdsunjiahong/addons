# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from datetime import datetime


class qdodoo_stock_inventory_wizard(models.Model):
    """
    生产库存盘点
    """
    _name = 'qdodoo.stock.inventory.wizard'
    _description = 'qdodoo.stock.inventory.wizard'

    def _get_company_id(self):
        return self.env['res.users'].browse(self.env.uid).company_id.id

    date = fields.Date(string=u'日期', required=True)
    inventory_id = fields.Many2one('stock.inventory', string=u'盘点表', required=True)
    debit_account = fields.Many2one('account.account', string=u'借方科目', required=True)
    credit_account = fields.Many2one('account.account', string=u'贷方科目', required=True)
    company_id = fields.Many2one('res.company', string=u'公司', default=_get_company_id, required=True)

    @api.multi
    def action_inventory(self):
        datetime_start = self.date + " 00:00:01"
        datetime_end = self.date + " 23:59:59"
        production_obj = self.env['mrp.production']
        product_inventory = {}
        product_list = []
        mrp_list = []
        mrp_dict = {}
        product_dict = {}
        return_list = []
        end_product_list = []
        end_product_dict = {}
        report_obj = self.env['qdodoo.stock.inventory.report2']
        account_move_line_obj = self.env['account.move.line']
        account_move_obj = self.env['account.move']
        product_obj = self.env['product.product']
        res_inventory = self.inventory_id.action_done()
        if self.inventory_id.line_ids:
            for move_id in self.inventory_id.move_ids:
                product_list.append(move_id.product_id.id)
                if move_id.location_id.id == self.inventory_id.location_id.id:
                    product_inventory[move_id.product_id.id] = -move_id.product_uom_qty

                else:
                    product_inventory[move_id.product_id.id] = move_id.product_uom_qty
        mrp_ids = production_obj.search(
            [('state', '=', 'done'), ('company_id', '=', self.company_id.id), ('date_planned', '>=', datetime_start),
             ('date_planned', '<=', datetime_end)])
        if not mrp_ids:
            raise except_orm(_(u'警告'), _(u'未找到生产单'))
        # 成品数量
        for mrp_id in mrp_ids:
            # if mrp_id.product_id.id in product_list:
            #     for mrp_cre_id in mrp_id.move_created_ids2:
            #         k = (mrp_cre_id, mrp_cre_id.product_id.id)
            #         mrp_list.append(k)
            #         mrp_dict[k] = mrp_id.product_qty
            #         product_id = mrp_cre_id.product_id.id
            #         product_dict[product_id] = product_dict.get(product_id, 0) + mrp_id.product_qty
            # else:
            # 原料数量
            if mrp_id.move_lines2:
                for move_l in mrp_id.move_lines2:
                    if move_l.product_id.id in product_list:
                        k = (move_l, move_l.product_id.id)
                        mrp_list.append(k)
                        mrp_dict[k] = move_l.product_uom_qty
                        product_id = move_l.product_id.id
                        product_dict[product_id] = product_dict.get(product_id, 0) + move_l.product_qty
        for mrp_l in mrp_list:
            difference_quantity = mrp_dict.get(mrp_l, 0) / product_dict.get(mrp_l[1], 0) * product_inventory.get(
                mrp_l[1], 0)
            k = (mrp_l[0].raw_material_production_id.id or mrp_l[0].production_id.id, mrp_l[1], self.inventory_id.id)
            if k in end_product_list:
                end_product_dict[k] += difference_quantity
            else:
                end_product_dict[k] = difference_quantity
                end_product_list.append(k)
        if res_inventory:
            # 查询对应的盘点明细
            account_move_lines = account_move_line_obj.search([('name', '=', 'INV:' + self.inventory_id.name)])
            # 删除所有的会计凭证
            account_lst = []
            account_line_lst = []
            if account_move_lines:
                for move_line in account_move_lines:
                    if move_line.move_id.id not in account_lst:
                        if move_line.move_id not in account_lst:
                            account_lst.append(move_line.move_id)
                        sql_d = """delete from account_move_line where id=%s"""%move_line.id
                        self._cr.execute(sql_d)
            for key_ll in end_product_list:
                if account_lst:
                    account_id = account_lst[0].copy({'ref':production_obj.browse(key_ll[0]).name})
                    val = {}
                    val['move_id'] = account_id.id
                    val['name'] = product_obj.browse(key_ll[1]).name
                    val['ref'] = product_obj.browse(key_ll[1]).name
                    val['journal_id'] = account_lst[0].journal_id.id
                    val['period_id'] = account_lst[0].period_id.id
                    val['account_id'] = self.debit_account.id
                    val['debit'] = abs(end_product_dict.get(key_ll, 0) * product_obj.browse(key_ll[1]).standard_price)
                    val['credit'] = 0
                    val['quantity'] = 1
                    val['date'] = datetime.now().date()
                    val['location_in_id'] = self.inventory_id.location_id.id
                    account_move_line_obj.create(val)
                    val['location_in_id'] = product_obj.browse(key_ll[1]).property_stock_production.id
                    val['account_id'] = self.credit_account.id
                    val['debit'] = 0
                    val['credit'] = abs(end_product_dict.get(key_ll, 0) * product_obj.browse(key_ll[1]).standard_price)
                    account_move_line_obj.create(val)
                data = {
                    'mo_id': key_ll[0],
                    'product_id': key_ll[1],
                    'product_qty': end_product_dict.get(key_ll, 0),
                    'inventory_id': key_ll[2],
                    'date': fields.Date.today(),
                    'debit_account': self.debit_account.id,
                    'credit_account': self.credit_account.id
                }
                res_obj = report_obj.create(data)
                return_list.append(res_obj.id)
        else:
            raise except_orm(_(u'警告'), _(u'盘点失败'))
        # 删除原有的会计凭证、明细
        for line in account_lst:
            line.unlink()
        if return_list:
            view_model, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_stock_inventory',
                                                                                 'qdodoo_stock_inventory_report2')
            return {
                'name': _('生产库存盘点表'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'qdodoo.stock.inventory.report2',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', return_list)],
                'views': [(view_id, 'tree')],
                'view_id': [view_id],
            }

        else:
            raise except_orm(_(u'警告'), _(u'未找到盘点数据'))
