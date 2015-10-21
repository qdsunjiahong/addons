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
                SELECT picking_id, po.id FROM stock_picking p, stock_move m, purchase_order_line pol, purchase_order po
                WHERE po.id = %s and po.id = pol.order_id and pol.id = m.purchase_line_id and m.picking_id = p.id
                GROUP BY picking_id, po.id

        """
            self.env.cr.execute(query, record.ids)
            picks = self.env.cr.fetchall()
            for pick_id, po_id in picks:
                pick_list = []
                pick_list.append(pick_id)
            if len(pick_list) > 1:
                state_list = []
                for pick_obj in picking_obj.browse(pick_list):
                    state_list.append(pick_obj.state)
                state_list_new = list(set(pick_list))
                if len(state_list_new) == 1 and state_list_new[0] == 'done':
                    record.stock_in_state = 'all_in'
                elif len(state_list_new) > 1 and 'done' in state_list_new:
                    record.stock_in_state = 'part_in'

            if len(pick_list) == 1:
                pick_obj = picking_obj.browse(pick_list[0])
                if pick_obj.state == 'done':
                    record.stock_in_state = 'all_in'
                else:
                    record.stock_in_state = 'not_in'

    stock_in_state = fields.Selection(
        [('not_in', u'未入库'), ('part_in', u'部分入库'), ('all_in', u'全部入库'), ('other', u'入库异常')], string=u'入库状态',
        compute='_compute_stock_state')
