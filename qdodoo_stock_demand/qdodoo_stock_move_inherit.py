# -*- encoding:utf-8 -*-

###########################################################################################
#
# module name for OpenERP
# Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import osv, fields

class qdodoo_stock_move_inerit(osv.osv):
    _inherit = 'stock.move'

    def _create_procurement(self, cr, uid, move, context=None):
        """ This will create a procurement order """
        procurement_obj = self.pool.get('procurement.order')
        if move.procurement_id.stock_demand_number:
            new_id = self.pool.get("procurement.order").create(cr, uid,
                                                               self._prepare_procurement_from_move(cr, uid, move,
                                                                                                   context=context),
                                                               context=context)
            procurement_obj.run(cr, uid, [new_id], context=context)
            return new_id
        else:
            return super(qdodoo_stock_move_inerit, self)._create_procurement(cr, uid, move, context=context)

    def _prepare_procurement_from_move(self, cr, uid, move, context=None):
        if move.procurement_id.stock_demand_number:
            origin = (move.group_id and (move.group_id.name + ":") or "") + (
                move.rule_id and move.rule_id.name or move.origin or "/")
            group_id = move.group_id and move.group_id.id or False
            if move.rule_id:
                if move.rule_id.group_propagation_option == 'fixed' and move.rule_id.group_id:
                    group_id = move.rule_id.group_id.id
                elif move.rule_id.group_propagation_option == 'none':
                    group_id = False
            return {
                'name': move.rule_id and move.rule_id.name or "/",
                'origin': origin,
                'company_id': move.company_id and move.company_id.id or False,
                'date_planned': move.date,
                'product_id': move.product_id.id,
                'product_qty': move.product_uom_qty,
                'product_uom': move.product_uom.id,
                'stock_demand_number': move.procurement_id.stock_demand_number,
                'order_id_new': move.procurement_id.order_id_new.id,
                'product_uos_qty': (move.product_uos and move.product_uos_qty) or move.product_uom_qty,
                'product_uos': (move.product_uos and move.product_uos.id) or move.product_uom.id,
                'location_id': move.location_id.id,
                'move_dest_id': move.id,
                'group_id': group_id,
                'route_ids': [(4, x.id) for x in move.route_ids],
                'warehouse_id': move.warehouse_id.id or (
                    move.picking_type_id and move.picking_type_id.warehouse_id.id or False),
                'priority': move.priority,
            }
        else:
            return super(qdodoo_stock_move_inerit, self)._prepare_procurement_from_move(cr, uid, move, context=context)
