# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:Qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, _, api, fields
from openerp.osv import osv

class tms_stowage(models.Model):
    """
        配载
    """
    _name = 'tms.stowage'

    name = fields.Char(u'配载单号')
    date = fields.Date(u'时间', default=lambda self:fields.date.today())
    car_id = fields.Many2one('tms.car.information',u'车辆')
    price = fields.Many2one('tms.car.information.price',u'基础费用')
    order_line = fields.One2many('tms.stowage.line','order_id',u'配载信息')
    state = fields.Selection([('draft',u'草稿'),('done',u'完成'),('cancel',u'取消')],u'状态',default='draft')

    # 完成
    @api.multi
    def btn_done(self):
        return self.write({'state':'done'})

    # 取消
    @api.multi
    def btn_cancel(self):
        for line in self.order_line:
            line.picking_id.write({'stowage_id':''})
        return self.write({'state':'cancel'})

class tms_stowage_line(models.Model):
    """
        配载明细
    """
    _name = 'tms.stowage.line'

    order_id = fields.Many2one('tms.stowage',u'配载')
    logistics_id = fields.Many2one('tms.trilateral.logistics',u'物流公司')
    portal_id = fields.Many2one('res.partner',u'门店')
    warm_box_num = fields.Integer(u'保温箱数')
    other_num = fields.Integer(u'其他数')
    portal_plus = fields.Float(u'门店加收费', compute='get_logistics_num')
    trilateral_logistics = fields.Float(u'物流短驳费', compute='get_logistics_num')
    warm_box_money = fields.Float(u'保温箱费用', compute='get_logistics_num')
    other_money = fields.Float(u'其他费用', compute='get_logistics_num')
    picking_id = fields.Many2one('stock.picking',u'调拨单')

    def get_logistics_num(self):
        for ids in self:
            if ids.logistics_id:
                ids.portal_plus = ids.portal_id.portal_plus
                ids.trilateral_logistics = ids.logistics_id.trilateral_add
                ids.warm_box_money = ids.portal_id.warm_box * ids.warm_box_num
                ids.other_money = ids.portal_id.tms_other * ids.other_num

class tms_stowage_wizard(models.TransientModel):
    """
        选择配载明细wizard
    """
    _name = 'tms.stowage.wizard'

    date_start = fields.Date(u'订单开始时间')
    date_end = fields.Date(u'订单结束时间')
    logistics_id = fields.Many2one('tms.trilateral.logistics',u'物流公司')
    portal_id = fields.Many2one('res.partner',u'门店')
    location_id = fields.Many2one('stock.warehouse',u'物流中心',related='logistics_id.location_id')


    @api.multi
    def btn_select(self):
        picking_obj = self.env['stock.picking']
        stowage_line_obj = self.env['tms.stowage.line']
        partner_obj = self.env['res.partner']
        domain = [('date','>=',self.date_start),('date','<=',self.date_end),('state','not in',('cancel','done')),('stowage_id','=',False)]
        if self.portal_id:
            domain.append(('partner_id','=',self.portal_id.id))
        else:
            partner_ids = partner_obj.search([('tms_location_id','=',self.logistics_id.location_id.id)])
            domain.append(('partner_id','in',partner_ids.ids))
        picking_ids = picking_obj.search(domain)
        if not picking_ids:
            raise osv.except_osv(_(u'警告'),_(u'未查询到对应的待出库数据！'))
        for picking_id in picking_ids:
            res_id = stowage_line_obj.create({'picking_id':picking_id.id,'order_id':self._context.get('active_id'),'logistics_id':self.logistics_id.id,'portal_id':picking_id.partner_id.id})
            picking_id.write({'stowage_id':res_id.id})
        return True

class tms_stock_picking_inherit(models.Model):
    """
        库存调拨增加标志字段是否已配载
    """
    _inherit = 'stock.picking'

    stowage_id = fields.Many2one('tms.stowage.line',u'配载明细')
