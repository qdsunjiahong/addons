# encoding:utf-8

from openerp import models, fields, api


class stock_quant_delete(models.Model):
    _name = 'stock.quant.delete'

    date_time = fields.Date(string=u'时间', required=True)

    @api.one
    def action_done(self):
        # 获取查询时间
        new_time = str(self.date_time) + " 00:00:01"
        # 查询所有运输库位
        location_ids = self.env['stock.location'].search([('usage', '=', 'transit')])
        location_list = []
        # 获取运输库位id列表
        for i in location_ids:
            location_list.append(i.id)
        # 循环所有运输库位id
        for location_id in location_list:
            # 查询目的库位是运输库位的调拨单（进入运输库位的）
            move_ids1 = self.env['stock.move'].search(
                [('location_dest_id', '=', location_id), ('date', '>=', new_time), ('state', '=', 'done')])
            # 查询源库位是运输库位的调拨单（出运输库位的）
            move_ids2 = self.env['stock.move'].search(
                [('location_id', '=', location_id), ('date', '>=', new_time), ('state', '=', 'done')])
            move_dict = {}
            # 循环所有进入运输库位的调拨单
            for move_id in move_ids1:
                # 如果产品在列表中
                if move_id.product_id.id in move_dict:
                    move_dict[move_id.product_id.id] += move_id.product_uom_qty
                else:
                    move_dict[move_id.product_id.id] = move_id.product_uom_qty
            # 循环所有出运输库位的调拨单
            for move_id2 in move_ids2:
                # 如果产品在列表中
                if move_id2.product_id.id in move_dict:
                    move_dict[move_id2.product_id.id] -= move_id2.product_uom_qty
                else:
                    move_dict[move_id2.product_id.id] = -move_id2.product_uom_qty

            quant_obj = self.env['stock.quant']
            quant_ids = quant_obj.search([('location_id', '=', location_id)])
            # 循环查询出来该库位的quant数据
            quant_id_lst = []
            for quant_id in quant_ids:
                if quant_id.product_id.id in quant_id_lst:
                    quant_id.unlink()
                else:
                    quant_id_lst.append(quant_id.product_id.id)
                    if move_dict.get(quant_id.product_id.id, 0) <= 0:
                        quant_id.write({'qty': 0.0})
                    else:
                        quant_id.write({'qty': move_dict.get(quant_id.product_id.id, 0.0)})
