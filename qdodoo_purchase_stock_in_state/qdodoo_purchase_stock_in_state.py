# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _

from openerp.exceptions import except_orm


class qdodoo_purchase_stock_state(models.Model):
    _inherit = 'purchase.order'

    @api.depends('picking_ids')
    def _compute_stock_state(self):
        picking_obj = self.env['stock.picking']
        for record in self:
            query = """
                SELECT p.id, po.id FROM stock_picking p, stock_move m, purchase_order_line pol, purchase_order po
                WHERE po.id = %s and po.id = pol.order_id and pol.id = m.purchase_line_id and m.picking_id = p.id and p.state = 'done'
                GROUP BY p.id, po.id,pol.order_id,pol.id,m.purchase_line_id,m.picking_id,p.state

        """
            self.env.cr.execute(query, tuple(record.ids))
            picks = self.env.cr.fetchall()
            pick_list = []
            po_list = []
            in_num = 0
            po_num = 0
            for pick_id, po_id in picks:
                pick_list.append(pick_id)
                po_list.append(po_id)
            for po_obj in self.browse(list(set(po_list))):
                for line_po in po_obj.order_line:
                    po_num += line_po.product_qty

            if pick_list:
                for pick_obj in picking_obj.browse(pick_list):
                    for move_l in pick_obj.move_lines:
                        in_num += move_l.product_uom_qty
                if po_num > in_num:
                    record.stock_in_state = 'part_in'
                else:
                    record.stock_in_state = 'all_in'


            else:
                record.stock_in_state = 'not_in'

    stock_in_state = fields.Selection(
        [('not_in', u'未入库'), ('part_in', u'部分入库'), ('all_in', u'全部入库'), ('other', u'入库异常')], string=u'入库状态',
        compute='_compute_stock_state', multi="purchase_stock")
