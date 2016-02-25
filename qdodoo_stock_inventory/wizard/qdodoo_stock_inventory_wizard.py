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
        # 组织过滤条件数据
        datetime_start = self.date + " 00:00:01"
        datetime_end = self.date + " 23:59:59"
        # 获取数据模型定义
        production_obj = self.env['mrp.production']
        account_move_line_obj = self.env['account.move.line']
        report_obj = self.env['qdodoo.stock.inventory.report2']
        # 审核盘点
        # 根据盘点表中辅助核算项修改明细中辅助核算项
        res_inventory = self.inventory_id.action_done()
        # 获取盘点的所有的产品id、根据库位获取产品对应数量
        product_list = []
        product_inventory = {}
        for move_id in self.inventory_id.move_ids:
            product_list.append(move_id.product_id.id)
            if move_id.location_id.id == self.inventory_id.location_id.id:
                product_inventory[move_id.product_id] = -move_id.product_uom_qty
            else:
                product_inventory[move_id.product_id] = move_id.product_uom_qty
        # 查询满足条件的
        mrp_ids = production_obj.search(
            [('state', '=', 'done'), ('company_id', '=', self.company_id.id), ('date_planned', '>=', datetime_start),
             ('date_planned', '<=', datetime_end)])
        if not mrp_ids:
            raise except_orm(_(u'警告'), _(u'未找到生产单'))
        # 获取已投料数量（盘点表中存在的产品）
        # 获取产品的所有数量
        # 获取所有生产单名字{id:名字}
        # 获取所有的产品明细{id:名字}
        mrp_dict = {} #{move_id:{产品:数量}}
        product_dict = {} #{产品:数量}
        mrp_name = {}
        for mrp_id in mrp_ids:
            mrp_name[mrp_id.id] = mrp_id.name
            mrp_dict[mrp_id] = {}
            for move_l in mrp_id.move_lines2:
                if move_l.product_id.id in product_list:
                    if move_l.product_id in mrp_dict[mrp_id]:
                        mrp_dict[mrp_id][move_l.product_id] += move_l.product_uom_qty
                    else:
                        mrp_dict[mrp_id][move_l.product_id] = move_l.product_uom_qty
                    product_dict[move_l.product_id] = product_dict.get(move_l.product_id, 0) + move_l.product_uom_qty
        # 组织均摊后的数据（按照生产单的比例计算）
        end_product_dict = {}
        for key,value in mrp_dict.items():
            end_product_dict[key] = {}
            for key1,value1 in value.items():
                end_product_dict[key][key1] = value1 / product_dict.get(key1) * product_inventory.get(key1)
        # 如果审核成功(获取所有凭证)
        # 获取创建的数据id
        return_list = []
        if res_inventory:
            # 查询对应的盘点明细
            account_move_lines = account_move_line_obj.search([('name', '=', 'INV:' + self.inventory_id.name)])
            # 删除已存在的会计凭证明细
            account_lst = []
            for move_line in account_move_lines:
                if move_line.move_id not in account_lst:
                    account_lst.append(move_line.move_id)
                    sql_d = """delete from account_move_line where id=%s"""%move_line.id
                    self._cr.execute(sql_d)

            for key_ll,value_ll in end_product_dict.items():
                for key_ll1,value_ll1 in value_ll.items():
                    # 如果有凭证，生成对应的凭证明细
                    if account_lst:
                        account_id = account_lst[0].copy({'ref':mrp_name.get(key_ll)})
                        val = {}
                        val['move_id'] = account_id.id
                        val['name'] = key_ll1.name
                        val['ref'] = key_ll1.name
                        val['journal_id'] = account_lst[0].journal_id.id
                        val['period_id'] = account_lst[0].period_id.id
                        if value_ll1 * key_ll1.standard_price >= 0:
                            val['account_id'] = self.debit_account.id
                        else:
                            val['account_id'] = self.credit_account.id
                        val['debit'] = abs(value_ll1 * key_ll1.standard_price)
                        val['credit'] = 0
                        val['quantity'] = value_ll1
                        val['date'] = datetime.now().date()
                        val['analytic_account_id'] = self.inventory_id.account_assistant.id
                        val['location_in_id'] = self.inventory_id.location_id.id
                        account_move_line_obj.create(val)
                        val['location_in_id'] = key_ll1.property_stock_production.id
                        if value_ll1 * key_ll1.standard_price <= 0:
                            val['account_id'] = self.debit_account.id
                        else:
                            val['account_id'] = self.credit_account.id
                        val['debit'] = 0
                        val['credit'] = abs(value_ll1 * key_ll1.standard_price)
                        val['analytic_account_id'] = self.inventory_id.account_assistant.id
                        account_move_line_obj.create(val)
                    data = {
                        'mo_id': key_ll.id,
                        'product_id': key_ll1.id,
                        'product_qty': value_ll1,
                        'inventory_id': self.inventory_id.id,
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