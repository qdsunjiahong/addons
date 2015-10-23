# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_stock_add_assistant(models.Model):
    _inherit = 'stock.inventory'

    account_assistant = fields.Many2one('account.analytic.account', string=u'辅助核算项')


class qdodoo_stock_purchase(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.product_qty')
    def _get_planned_quantity(self):
        for record in self:
            record.planned_quantity = sum(line.product_qty for line in record.order_line)

    @api.depends('picking_ids')
    def _get_arrival_quantity(self):
        picking_obj = self.env['stock.picking']
        for record in self:
            query = """
                SELECT picking_id, po.id FROM stock_picking p, stock_move m, purchase_order_line pol, purchase_order po
                WHERE po.id = %s and po.id = pol.order_id and pol.id = m.purchase_line_id and m.picking_id = p.id and p.state = 'done'
                GROUP BY picking_id, po.id
                """
            self.env.cr.execute(query, tuple(record.ids))
            picks = self.env.cr.fetchall()
            pick_list = []
            if picks:
                for pick_id, po_id in picks:
                    pick_list.append(pick_id)

            if pick_list:
                arrival_quantity = 0
                for picking_id in picking_obj.browse(pick_list):
                    for line in picking_id.move_lines:
                        arrival_quantity += line.product_uom_qty
                record.arrival_quantity = arrival_quantity
            else:
                record.arrival_quantity = 0

    @api.one
    def _get_storage_reminder(self):
        for record in self:
            if record.arrival_quantity < record.planned_quantity and record.deal_date <= fields.Date.today():
                record.storage_reminder = True

    planned_quantity = fields.Float(digits=(16, 4), string=u'计划数量', compute="_get_planned_quantity",
                                    multi='storage_reminder')
    arrival_quantity = fields.Float(digits=(16, 4), string=u'到期数量', compute='_get_arrival_quantity',
                                    multi='storage_reminder')
    storage_reminder = fields.Boolean(string=u'入库提醒', compute="_get_storage_reminder", multi='storage_reminder')
