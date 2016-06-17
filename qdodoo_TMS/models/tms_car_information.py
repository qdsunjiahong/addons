# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:Qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, _, api, fields

class tms_car_information(models.Model):
    """
        车辆档案
    """
    _name = 'tms.car.information'
    _rec_name = 'rec_name'

    name = fields.Char(u'编码')
    car_num = fields.Char(u'车牌号')
    owner = fields.Many2one('res.partner',u'车主')
    rec_name = fields.Char(u'名称',compute='get_rec_name')
    car_type = fields.Char(u'车型')
    location_id = fields.Many2one('stock.warehouse',u'物流中心')
    car_phone = fields.Char(u'联系电话')
    car_carid = fields.Char(u'身份证号')
    driver = fields.Char(u'司机')
    driver_phone = fields.Char(u'联系电话')
    driver_carid = fields.Char(u'身份证号')
    price_line = fields.One2many('tms.car.information.price','tms_id',u'起步价')
    warm_box = fields.Float(u'保温箱')
    other = fields.Float(u'其他')
    piece = fields.Float(u'件')

    # 计算车辆显示名字 [编码]车牌号(车主)
    @api.multi
    def get_rec_name(self):
        for ids in self:
            ids.rec_name = '[' + ids.name + ']' + ids.car_num + '(' + ids.owner.name + ')'

    # 选择车主后，默认关联司机为本人
    @api.onchange('owner')
    def onchange_owner(self):
        if self.owner:
            self.driver = self.owner.name
        else:
            self.driver = ''

class tms_car_information_price(models.Model):
    """
        车辆起步价
    """
    _name = 'tms.car.information.price'

    tms_id = fields.Many2one('tms.car.information',u'车辆档案')
    name = fields.Float(u'起步价')