# encoding:utf-8

from openerp import models, fields, api


class stock_quant_delete(models.Model):
    _name = 'stock.quant.delete'

    date_time = fields.Date(string=u'时间')

    @api.one
    def action_done(self):
        new_time = str(self.date_time) + " 00:00:01"
        location_ids = self.env['stock.location'].search([('usage', '=', 'transit')])
        location_list = []
        for i in location_ids:
            location_list.append(i.id)
        for location_id in location_list:
            move_ids1 = self.env['stock.move'].search(
                [('location_dest_id', '=', location_id), ('create_date', '>=', new_time), ('state', '=', 'done')])
            move_ids2 = self.env['stock.move'].search(
                [('location_id', '=', location_id), ('create_date', '>=', new_time), ('state', '=', 'done')])
            move_dict = {}
            product_list = []
            for move_id in move_ids1:
                if move_id.product_id.id in product_list:
                    move_dict[move_id.product_id.id] += move_id.product_uom_qty
                else:
                    move_dict[move_id.product_id.id] = move_id.product_uom_qty
                    product_list.append(move_id.product_id.id)
            for move_id2 in move_ids2:
                if move_id2.product_id.id in product_list:
                    move_dict[move_id2.product_id.id] -= move_id2.product_uom_qty
                else:
                    move_dict[move_id2.product_id.id] = -move_id2.product_uom_qty
                    product_list.append(move_id2.product_id.id)
            quant_obj = self.env['stock.quant']
            quant_ids = quant_obj.search([('location_id', '=', location_id)])
            for quant_id in quant_ids:
                if quant_id.product_id.id in product_list:
                    quant_id.write({'qty': move_dict.get(quant_id.product_id.id, 0.0)})
                else:
                    quant_id.write({'qty': 0.0})
