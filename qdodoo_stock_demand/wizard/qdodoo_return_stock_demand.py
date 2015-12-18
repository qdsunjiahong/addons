# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_stock_return_picking(models.Model):
    """
    增加需求单反转功能
    """
    _inherit = 'stock.return.picking'

    @api.multi
    def create_demand_returns2(self):
        context = self._context or {}
        record_id = context and context.get('active_id', False) or False
        picking_obj = self.env['stock.picking']
        procurement_obj = self.env['procurement.rule']
        picking_id = picking_obj.browse(record_id)
        product_return_moves = self.product_return_moves or []
        if product_return_moves:
            move_lines_obj = picking_id.move_lines[0]
            # 需求转换单ID
            demand_id = move_lines_obj.procurement_id.order_id_new or False
            # 源需求转换单route库位
            location_dest_id = []
            # 中间库位
            inter_location_id = []
            if not demand_id:
                raise except_orm(_(u'警告'), _(u'只能操作通过需求转换单来的单据'))
            route_id = demand_id.route_id
            for rule_l in demand_id.route_id.pull_ids:
                if rule_l.picking_type_id.code == 'outgoing':
                    # 逆推目的库位
                    location_id = rule_l.location_src_id.id
                    location_dest_id.append(location_id)
                    inter_location_id.append(rule_l.location_id.id)

            ware_obj = self.env['stock.warehouse']
            # # 目的仓库的入库类型
            location_view_id = self.return_location_view_id(self.env['stock.location'].browse(location_dest_id[0]))
            ware_id = ware_obj.search([('view_location_id', '=', location_view_id)])
            route_list1 = []
            route_list2 = []
            if ware_id.reception_steps == 'one_step':
                pull_id1 = route_id.pull_ids[0]
                pull_id2 = route_id.pull_ids[1]
                domain1 = [('location_src_id', '=', pull_id1.location_id.id),
                           ('location_id', '=', pull_id1.location_src_id.id),
                           ('action', '=', 'move'), ('route_id', '!=', False)]
                domain2 = [('location_src_id', '=', pull_id2.location_id.id),
                           ('location_id', '=', pull_id2.location_src_id.id),
                           ('action', '=', 'move'), ('route_id', '!=', False)]
                rule_ids1 = procurement_obj.search(domain1)
                for rule_id1 in rule_ids1:
                    route_list1.append(rule_id1.route_id.id)
                rule_ids2 = procurement_obj.search(domain2)
                for rule_id2 in rule_ids2:
                    route_list2.append(rule_id2.route_id.id)

            else:
                # #### 逆推路线#####
                # # 源库位
                location_src_id = picking_id.move_lines[0].location_dest_id.id
                domain = [('location_src_id', '=', location_src_id), ('location_id', '=', inter_location_id[0]),
                          ('action', '=', 'move'), ('route_id', '!=', False)]
                rule_id1 = procurement_obj.search(domain)
                ware_id_src = self.return_location_view_id(picking_id.move_lines[0].location_dest_id)
                ware_id2 = ware_obj.search([('view_location_id', '=', ware_id_src)])
                cash_location = ware_id.wh_input_stock_loc_id.id
                rule_id2 = procurement_obj.search(
                    [('location_src_id', '=', inter_location_id[0]), ('location_id', '=', cash_location),
                     ('action', '=', 'move'), ('route_id', '!=', False)])

                route_list1 = [x.route_id.id for x in rule_id1]
                route_list2 = [y.route_id.id for y in rule_id2]
            route_list = []
            for i in route_list1:
                if i in route_list2:
                    route_list.append(i)
            if not route_list:
                raise except_orm(_(u'警告'), _(u'路线%s>>%s未设置，请先到仓库进行设置') % (ware_id2.name, ware_id.name))
            elif len(route_list) > 1:
                raise except_orm(_(u'警告'), _(u'数据有误'))

            move_lines = []
            for return_line in product_return_moves:
                if return_line.quantity > 0:
                    res = self._prapare_demand_line(return_line)
                    move_lines.append(res)

            data = {
                'name': '/',
                'partner_id': picking_id.partner_id.id or False,
                'location_id': ware_id.id,
                'location_id2': location_dest_id[0],
                'priority_new': '1',
                'group_id': picking_id.group_id.id,
                'qdodoo_stock_product_ids': move_lines,
                'demand_id': demand_id.id or False,
                'route_id': route_list[0],
            }
            create_obj = self.env['qdodoo.stock.demand'].create(data)
            picking_id.write({'demand_bool': True})
            from_model, from_id = self.env['ir.model.data'].get_object_reference('qdodoo_stock_demand',
                                                                                 'view_form_qdodoo_stock_demand')
            tree_model, tree_id = self.env['ir.model.data'].get_object_reference('qdodoo_stock_demand',
                                                                                 'view_tree_qdodoo_stock_demand2')
            return {
                'name': _(u'需求转换单'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'qdodoo.stock.demand',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', [create_obj.id])],
                'views': [(tree_id, 'tree'), (from_id, 'form')],
                'view_id': [tree_id],
            }

    @api.model
    def return_location_view_id(self, location_id):
        if location_id.usage == 'view':
            return location_id.id
        else:
            return self.return_location_view_id(location_id.location_id)

    @api.model
    def _prapare_demand_line(self, move_line):
        data = {
            'product_id': move_line.product_id.id,
            'product_qty': move_line.quantity,
            'name': move_line.product_id.name_template,
            'uom_id': move_line.product_id.uom_id.id
        }
        return (0, 0, data)

    def _search_suitable_rule(self, cr, uid, procurement, domain, context=None):
        '''we try to first find a rule among the ones defined on the procurement order group and if none is found, we try on the routes defined for the product, and finally we fallback on the default behavior'''
        pull_obj = self.pool.get('procurement.rule')
        warehouse_route_ids = []
        if procurement.warehouse_id:
            domain += ['|', ('warehouse_id', '=', procurement.warehouse_id.id), ('warehouse_id', '=', False)]
            warehouse_route_ids = [x.id for x in procurement.warehouse_id.route_ids]

        # 产品路线
        product_route_ids = [x.id for x in
                             procurement.product_id.route_ids + procurement.product_id.categ_id.total_route_ids]
        # 需求单路线
        procurement_route_ids = [x.id for x in procurement.route_ids]
        res = pull_obj.search(cr, uid, domain + [('route_id', 'in', procurement_route_ids)],
                              order='route_sequence, sequence', context=context)
        if not res:
            res = pull_obj.search(cr, uid, domain + [('route_id', 'in', product_route_ids)],
                                  order='route_sequence, sequence', context=context)
            if not res:
                res = warehouse_route_ids and pull_obj.search(cr, uid,
                                                              domain + [('route_id', 'in', warehouse_route_ids)],
                                                              order='route_sequence, sequence', context=context) or []
                if not res:
                    res = pull_obj.search(cr, uid, domain + [('route_id', '=', False)], order='sequence',
                                          context=context)
        return res


class qdodoo_stock_picking(models.Model):
    _inherit = 'stock.picking'

    demand_bool = fields.Boolean(string=u'需求反转')
