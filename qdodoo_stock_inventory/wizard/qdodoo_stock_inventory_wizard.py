# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


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
    company_id = fields.Many2one('res.company', string=u'公司', default=_get_company_id, required=True)

    @api.multi
    def action_inventory(self):
        if self.inventory_id.inventory_b == True:
            raise except_orm(_(u'警告'), _(u'盘点表%已盘点') % self.inventory_id.name)
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
            if mrp_id.product_id.id in product_list:
                for mrp_cre_id in mrp_id.move_created_ids2:
                    k = (mrp_cre_id, mrp_cre_id.product_id.id)
                    mrp_list.append(k)
                    mrp_dict[k] = mrp_id.product_qty
                    product_id = mrp_cre_id.product_id.id
                    product_dict[product_id] = product_dict.get(product_id, 0) + mrp_id.product_qty
            else:
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
        for key_ll in end_product_list:
            data = {
                'mo_id': key_ll[0],
                'product_id': key_ll[1],
                'product_qty': end_product_dict.get(key_ll, 0),
                'inventory_id': key_ll[2],
                'date': fields.Date.today(),
            }
            res_obj = report_obj.create(data)
            return_list.append(res_obj.id)
        if return_list:
            self.inventory_id.write({'inventory_b': True})
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


class qdodoo_stock_inventory_inherit(models.Model):
    _inherit = 'stock.inventory'

    inventory_b = fields.Boolean(string=u'生产盘点完成', copy=False)
