# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
import time
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_merge_yf_order(models.Model):
    _name = 'qdodoo.merge.yf.order'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """
         Changes the view dynamically
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view.
        """
        if context is None:
            context={}

        res = super(qdodoo_merge_yf_order, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context.get('active_model','') == 'purchase.order' and len(context['active_ids']) < 2:
            raise osv.except_osv(_('警告!'),_('请至少选择两条数据.'))
        return res

    # 合并运费单
    def btn_merge(self, cr, uid, ids, context=None):
        purchase_obj = self.pool.get('purchase.order')
        partner_lst = []
        num_volume = 0
        num_weight = 0
        origin = ''
        for line in purchase_obj.browse(cr, uid, context.get('active_ids')):
            if line.is_logistics == False:
                raise osv.except_osv(_('警告!'),_('只能合并运费单.'))
            if line.state != 'draft':
                raise osv.except_osv(_('警告!'),_('只能合并草稿状态的运费单.'))
            if line.partner_id.id not in partner_lst:
                partner_lst.append(line.partner_id.id)
                if len(partner_lst) >= 2:
                     raise osv.except_osv(_('警告!'),_('只能合并相同供应商的运费单.'))
            num_volume += line.volume_order
            num_weight += line.weight_order
            if not origin:
                origin = line.picking_out_origin
            else:
                origin  = origin + ';' + line.picking_out_origin
        purchase_obj.write(cr, uid, context.get('active_ids')[0],{'picking_out_origin':origin,'volume_order':num_volume,'weight_order':num_weight,})
        purchase_obj.write(cr, uid, context.get('active_ids')[1:],{'state':'cancel'})
        return True

class qdodoo_purchase_order_inherit(models.Model):
    """
        物流运费模块,运输单
    """
    _inherit = 'purchase.order'    # 继承

    is_logistics = fields.Boolean(u'是否为运费单')
    picking_out_id = fields.Many2one('stock.picking',string='出库单')
    picking_out_origin = fields.Char(string='出库单',readonly=True)
    volume_order = fields.Float(u'体积方数')
    weight_order = fields.Float(u'重量')
    all_volume = fields.Float(u'满载方数')
    all_volume_rate = fields.Float(u'满载率',compute='_get_all_volume_rate')
    location_id_tfs = fields.Many2one('stock.location',u'源库位')
    location_dest_id_tfs = fields.Many2one('stock.location',u'目标库位')
    shipper_tfs = fields.Many2one('delivery.carrier',u'车型')
    invoice_state = fields.Selection([('draft',u'草稿'),
            ('proforma',u'形式发票'),
            ('proforma2',u'形式发票'),
            ('open',u'待支付'),
            ('paid',u'已付'),
            ('cancel',u'已取消'),],u'发票状态',compute='_get_state')

    _defaults={
            "is_logistics":False,
            }

    # 获取对应的发票状态
    def _get_state(self):
        for ids in self:
            # 获取关联的发票
            for id in ids.invoice_ids:
                ids.invoice_state = id.state

    # 获取满载率
    def _get_all_volume_rate(self):
        for line in self:
            if line.all_volume:
                line.all_volume_rate = line.volume_order / line.all_volume
            else:
                line.all_volume_rate = 0

    # 查看出库单
    def read_picking_out(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        stock_obj = self.pool.get('stock.picking')
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'stock', 'vpicktree')
        res_form = mod_obj.get_object_reference(cr, uid, 'stock', 'view_picking_form')
        res_id = res and res[1] or False
        res_form_id = res_form and res_form[1] or False
        inv_ids = []
        if obj.picking_out_origin:
            for line in obj.picking_out_origin.split(';'):
                inv_ids += stock_obj.search(cr, uid, [('name','=',line)])
        return  {
            'name': _('出库单'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': [res_id],
            'views': [(res_id,'tree'),(res_form_id,'form')],
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [('id','in',inv_ids)],
        }

class qdodoo_stock_picking_inherit(models.Model):
    """
        物流运费模块，出货单修改
    """
    _inherit = 'stock.picking'    # 继承

    shipper = fields.Many2one('delivery.carrier', string='承运方')
    shipper_num = fields.Char(string='承运方跟踪号')
    delivery_grid = fields.Many2one('delivery.grid',string='收货地点')
    is_delivery_grid = fields.Boolean(related='shipper.use_detailed_pricelist',string='收货地点')

    def onchange_get_delivery_grid(self, cr, uid, ids, shipper):
        if shipper:
            return {'value':{'delivery_grid':False}}

    @api.cr_uid_ids_context
    def do_transfer(self, cr, uid, picking_ids, context=None):
        res = super(qdodoo_stock_picking_inherit,self).do_transfer(cr, uid, picking_ids, context=context)
        if res:
            for obj in self.browse(cr, uid, picking_ids):
                # 判断如果调拨单类型是出库单 并且 存在承运方
                if obj.picking_type_id.code == 'outgoing' and obj.shipper:
                    # 创建运费单
                    purchase_obj = self.pool.get('purchase.order')
                    purchase_line_obj = self.pool.get('purchase.order.line')
                    partner = self.pool.get('res.partner')
                    supplier = partner.browse(cr, uid, obj.shipper.partner_id.id, context=context)
                    vals = {}
                    location_id = ''
                    location_dest_id = ''
                    vals['partner_id'] = obj.shipper.partner_id.id
                    vals['pricelist_id'] = supplier.property_product_pricelist_purchase.id
                    vals['fiscal_position'] = supplier.property_account_position and supplier.property_account_position.id or False
                    for location in obj.move_lines:
                        location_id = location.location_id.id
                        location_dest_id = location.location_dest_id.id
                    vals['all_volume'] = obj.shipper.all_volume
                    vals['location_id'] = location_dest_id
                    vals['origin'] = obj.origin
                    vals['shipper_tfs'] = obj.shipper.id
                    vals['location_id_tfs'] = location_id
                    vals['location_dest_id_tfs'] = location_dest_id
                    vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'qdodoo.logistics.freight')
                    vals['is_logistics'] = True
                    # vals['picking_out_id'] = obj.id
                    vals['picking_out_origin'] = obj.name
                    sum = 0
                    sum_weight = 0
                    for line in obj.pack_operation_ids:
                        sum += line.product_id.volume * line.product_qty
                        sum_weight += line.product_id.weight * line.product_qty
                    vals['volume_order'] = sum
                    vals['weight_order'] = sum_weight
                    vals['invoice_method'] = 'order'
                    res_id = purchase_obj.create(cr, uid, vals, context=context)
                    val = {}
                    normal_price = obj.shipper.normal_price
                    if obj.shipper.use_detailed_pricelist:
                        for line_id in obj.delivery_grid.line_ids:
                            if line_id.type == 'weight':
                                if eval(str(sum_weight) + line_id.operator + str(line_id.max_value)):
                                    normal_price = line_id.standard_price * sum_weight
                                    break
                            elif line_id.type == 'volume':
                                if eval(str(sum) + line_id.operator + str(line_id.max_value)):
                                    normal_price = line_id.standard_price * sum
                                    break
                    val['product_id'] = obj.shipper.product_id.id
                    val['name'] = obj.shipper.product_id.name
                    val['company_id'] = obj.company_id.id
                    val['product_qty'] = 1
                    val['product_uom'] = obj.shipper.product_id.uom_id.id
                    val['price_unit'] = normal_price
                    val['order_id'] = res_id
                    val['date_planned'] = datetime.now()
                    purchase_line_obj.create(cr, uid, val, context=context)
                    return True

class qdodoo_delivery_carrier_tfs(models.Model):
    _inherit = 'delivery.carrier'

    all_volume = fields.Float(u'满载方数(m³)')


