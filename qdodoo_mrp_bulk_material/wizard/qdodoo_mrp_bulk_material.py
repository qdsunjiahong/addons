# encoding:utf-8
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_mrp_bulk_material(models.Model):
    _name = 'mrp.bulk.material'

    localtion_dest_id = fields.Many2one('stock.location', required=True, string=u'源库位')
    location_id = fields.Many2one('stock.location', required=True, string=u'目的库位')
    mrp_ids = fields.Char(string=u'生产订单ID', required=True)

    def _default_get_mrp_ids(self, cr, uid, context=None):
        mrp_ids = ''
        if context.get('active_model') == 'mrp.production':
            active_ids = context.get('active_ids', []) or []
            prodcution_obj = self.pool.get('mrp.production')
            for i in prodcution_obj.browse(cr, uid, active_ids, context=context):
                mrp_ids += str(i.id) + ';'
            return mrp_ids[0:-1]

    _defaults = {
        'mrp_ids': _default_get_mrp_ids,
    }

    @api.one
    def action_done(self):
        """
        批量领料方法
        """
        company_ids = []
        product_list = []
        product_dict = {}  # key=产品id,value=产品数量
        mrp_production_obj = self.env['mrp.production']
        mrp_ids = self.mrp_ids.split(';')  # 分割mrp_ids得到生产订单ID列表
        for mrp_id in mrp_ids:
            mrp_production = mrp_production_obj.browse(int(mrp_id))
            company_ids.append(mrp_production.company_id.id)
            if mrp_production.state == 'done':
                raise except_orm(_(u'警告'), _(u'你不能选择已完成的生产单！'))
            else:
                if mrp_production.move_lines:
                    for move_line in mrp_production.move_lines:
                        if move_line.product_id.id in product_dict:
                            product_dict[move_line.product_id.id] += move_line.product_uom_qty
                        else:
                            product_dict[move_line.product_id.id] = move_line.product_uom_qty
                else:
                    if not mrp_production.bom_id.bom_line_ids:
                        raise except_orm(_(u'警告'), _(u'生产订单%s未关联物料清单或者关联物料清单没有部件明细！') % (mrp_production.name))
                    for bom_line in mrp_production.bom_id.bom_line_ids:
                        if bom_line.product_id.id in product_dict:
                            product_dict[bom_line.product_id.id] += bom_line.product_qty * (
                                mrp_production.product_qty / mrp_production.bom_id.product_qty)
        if len(list(set(company_ids))) > 1:
            raise except_orm(_(u'警告'), _(u'只能选择同一个公司的生产单'))
        for key in product_dict.keys():
            lines = {
                'product_id': key,
                'product_uom_qty': product_dict[key] or 0.0,
                'name': self.env['product.product'].browse(key).name or '',
                'product_uom': self.env['product.product'].browse(key).uom_id.id,
                'location_id': self.localtion_dest_id.id,
                'location_dest_id': self.location_id.id,
            }
            product_list.append((0, 0, lines))
        pick_type_ids = self.env['stock.picking.type'].search(
            [('default_location_src_id', '=', self.localtion_dest_id.id),
             ('code', 'in', ('outgoing', 'internal')),
             ('default_location_dest_id', '=', self.location_id.id)])
        if len(pick_type_ids) == 1:

            picking_dict = {
                'picking_type_id': pick_type_ids.id,
                'origin': u'批量领料',
                'move_lines': product_list,
            }
            self.env['stock.picking'].create(picking_dict)
        elif len(pick_type_ids) > 2:
            raise except_orm(_(u'警告'),
                             _(u'源库位为%s，目的库位为%s的拣货单类型搜索出多个') % (self.localtion_dest_id.name, self.location_id.name))
        else:
            raise except_orm(_(u'警告'),
                             _(u'源库位为%s，目的库位为%s的拣货单类型未创建') % (self.localtion_dest_id.name, self.location_id.name))
