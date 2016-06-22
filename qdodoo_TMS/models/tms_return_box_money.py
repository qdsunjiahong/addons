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

class tms_return_box_money(models.Model):
    """
        回箱和特殊运费
    """
    _name = 'tms.return.box.money'

    name = fields.Date(u'日期')
    car_id = fields.Many2one('tms.car.information',u'车辆')
    money_type = fields.Selection([('return_box',u'回箱'),('special',u'特殊运费')],u'类型')
    order_line = fields.One2many('tms.return.box.money.line','order_id',u'明细')
    state = fields.Selection([('draft',u'草稿'),('done',u'完成'),('cancel',u'取消')],u'状态',default='draft')
    order_line2 = fields.One2many('tms.return.box.money.line2','order_id',u'明细')

    # 完成
    @api.multi
    def btn_done(self):
        return self.write({'state':'done'})

    # 取消
    @api.multi
    def btn_cancel(self):
        return self.write({'state':'cancel'})

class tms_return_box_money_line(models.Model):
    """
        回箱和特殊运费明细
    """
    _name = 'tms.return.box.money.line'

    order_id = fields.Many2one('tms.return.box.money',u'费用')
    logistics_id = fields.Many2one('tms.trilateral.logistics',u'物流名称')
    location_id = fields.Many2one('stock.warehouse',u'物流中心',related='logistics_id.location_id')
    portal_id = fields.Many2one('res.partner',u'门店')
    return_box_num = fields.Float(u'回箱数')
    return_box_standard = fields.Float(u'回箱标准')
    return_box_money = fields.Float(u'回箱费用', compute='get_money')
    return_box_partner = fields.Selection([('portal',u'门店垫付'),('driver',u'司机垫付'),('trilateral',u'第三方物流月结'),('payment',u'现付'),('free',u'免费')],u'回箱付款方')

    # 获取回箱标准
    @api.onchange('portal_id')
    def onchange_portal_id(self):
        if self.portal_id:
            self.return_box_standard = self.portal_id.warm_box

    # 计算回箱费用
    def get_money(self):
        for ids in self:
            ids.return_box_money = ids.return_box_num * ids.return_box_standard

class tms_return_box_money_line2(models.Model):
    """
        回箱和特殊运费明细
    """
    _name = 'tms.return.box.money.line2'

    order_id = fields.Many2one('tms.return.box.money',u'费用')
    logistics_id = fields.Many2one('tms.trilateral.logistics',u'物流名称')
    location_id = fields.Many2one('stock.warehouse',u'物流中心',related='logistics_id.location_id')
    portal_id = fields.Many2one('res.partner',u'门店')
    return_box_partner = fields.Selection([('portal',u'门店垫付'),('driver',u'司机垫付'),('trilateral',u'第三方物流月结'),('payment',u'现付'),('free',u'免费')],u'特单付款方')
    special_result = fields.Selection([('trilateral',u'第三方物流临时变更'),('logistics',u'运费价格临时变更'),('over_time',u'超时加单'),('box',u'退换箱'),('address',u'收货地址变更'),
                                       ('empty_box',u'专车反空箱'),('warm_box',u'保温箱扣款'),('portal',u'门店扣款'),('other',u'其他')],u'特单原因')
    jyg_assume = fields.Float(u'金银花承担')
    trilateral_assume = fields.Float(u'物流承担')
    portal_assume = fields.Float(u'门店承担')
    all_assume = fields.Float(u'合计承担')
    payment_money = fields.Float(u'付款金额')
    note = fields.Char(u'备注')