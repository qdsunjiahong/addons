# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models
from openerp.osv import osv
import time
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_promotion(models.Model):
    """
        促销单
    """
    _name = 'qdodoo.promotion'    # 模型名称
    _description = 'qdodoo.promotion'    # 模型描述

    name = fields.Char(u'方案名称',required=True)
    selection_ids = fields.Selection([('reduction',u'满减促销'),('gift',u'满赠促销'),('discount',u'打折促销')],u'促销类型')
    version_gift_id = fields.One2many('qdodoo.promotion.version.gift','promotion_id',string=u'方案版本')
    version_id = fields.One2many('qdodoo.promotion.version','promotion_id',string=u'方案版本')
    version_discount_id = fields.One2many('qdodoo.promotion.version.discount','promotion_id',string=u'方案版本')
    active = fields.Boolean(u'有效')
    company_id = fields.Many2one('res.company',u'公司',required=True)
    is_play = fields.Boolean(u'是否让客户自己报名')

    _defaults = {
        'active':True,
        'is_play':True,
        'company_id': lambda self, cr, uid, ids, context=None:self.pool.get('res.users').browse(cr, uid, uid).company_id.id
    }

    def create(self, cr, uid, valus, context=None):
        selection_ids = valus.get('selection_ids')
        if selection_ids:
            self_ids = self.search(cr, uid, [('selection_ids','=',selection_ids)])
            # if self_ids:
            #     raise osv.except_osv(_('错误!'), _("此促销类型已存在."))
        return super(qdodoo_promotion, self).create(cr, uid, valus, context=context)

class qdodoo_promotion_version_gift(models.Model):
    """
        满赠促销版本
    """
    _name = 'qdodoo.promotion.version.gift'

    promotion_id = fields.Many2one('qdodoo.promotion',u'促销单')
    name = fields.Char(u'版本名称',required=True)
    date_start = fields.Date(u'开始时间')
    date_end = fields.Date(u'结束时间')
    active = fields.Boolean(u'有效')
    items_id = fields.One2many('qdodoo.promotion.version.gift.items','version_id',u'优惠条目')

    _defaults = {
        'active':True,
    }

    def create(self, cr, uid, valus, context=None):
        # promotion_obj = self.pool.get('qdodoo.promotion')
        promotion_id = valus.get('promotion_id')
        date_start = valus.get('date_start')
        date_end = valus.get('date_end')
        if promotion_id:
            self_ids = self.search(cr, uid, [('promotion_id','=',promotion_id)])
            if self_ids:
                for line in self.browse(cr, uid, self_ids):
                    # 如果开始时间没填
                    if not date_start:
                        if not date_end:
                            raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
                        else:
                            if date_end <= line.date_start or not line.date_start:
                                raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
                    else:
                        if not date_end:
                            if date_start >= line.date_end or not line.date_end:
                                raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
                        else:
                            if (line.date_start <= date_start <= line.date_end) or (line.date_start <= date_end <= line.date_end) or (not line.date_end) or (not line.date_start):
                                raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
        return super(qdodoo_promotion_version_gift, self).create(cr, uid, valus, context=context)

class qdodoo_promotion_version_discount(models.Model):
    """
        打折促销版本
    """
    _name = 'qdodoo.promotion.version.discount'

    promotion_id = fields.Many2one('qdodoo.promotion',u'促销单')
    name = fields.Char(u'版本名称',required=True)
    date_start = fields.Date(u'开始时间')
    date_end = fields.Date(u'结束时间')
    active = fields.Boolean(u'有效', default=True)
    items_id = fields.One2many('qdodoo.promotion.version.discount.items','version_id',u'优惠条目')

    def create(self, cr, uid, valus, context=None):
        # promotion_obj = self.pool.get('qdodoo.promotion')
        promotion_id = valus.get('promotion_id')
        date_start = valus.get('date_start')
        date_end = valus.get('date_end')
        if promotion_id:
            self_ids = self.search(cr, uid, [('promotion_id','=',promotion_id)])
            if self_ids:
                for line in self.browse(cr, uid, self_ids):
                    # 如果开始时间没填
                    if not date_start:
                        if not date_end:
                            raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
                        else:
                            if date_end <= line.date_start or not line.date_start:
                                raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
                    else:
                        if not date_end:
                            if date_start >= line.date_end or not line.date_end:
                                raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
                        else:
                            if (line.date_start <= date_start <= line.date_end) or (line.date_start <= date_end <= line.date_end) or (not line.date_end) or (not line.date_start):
                                raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
        return super(qdodoo_promotion_version_discount, self).create(cr, uid, valus, context=context)

class qdodoo_promotion_version(models.Model):
    """
        满减促销
    """
    _name = 'qdodoo.promotion.version'

    promotion_id = fields.Many2one('qdodoo.promotion',u'促销单')
    name = fields.Char(u'版本名称',required=True)
    date_start = fields.Date(u'开始时间')
    date_end = fields.Date(u'结束时间')
    active = fields.Boolean(u'有效', default=True)
    items_id = fields.One2many('qdodoo.promotion.version.items','version_id',u'优惠条目')

    def create(self, cr, uid, valus, context=None):
        # promotion_obj = self.pool.get('qdodoo.promotion')
        promotion_id = valus.get('promotion_id')
        date_start = valus.get('date_start')
        date_end = valus.get('date_end')
        if promotion_id:
            self_ids = self.search(cr, uid, [('promotion_id','=',promotion_id)])
            if self_ids:
                for line in self.browse(cr, uid, self_ids):
                    # 如果开始时间没填
                    if not date_start:
                        if not date_end:
                            raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
                        else:
                            if date_end <= line.date_start or not line.date_start:
                                raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
                    else:
                        if not date_end:
                            if date_start >= line.date_end or not line.date_end:
                                raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
                        else:
                            if (line.date_start <= date_start <= line.date_end) or (line.date_start <= date_end <= line.date_end) or (not line.date_end) or (not line.date_start):
                                raise osv.except_osv(_('错误!'), _("版本的时间段不能出现重叠."))
        return super(qdodoo_promotion_version, self).create(cr, uid, valus, context=context)

class qdodoo_promotion_version_items(models.Model):
    """
        满减促销明细
    """
    _name = 'qdodoo.promotion.version.items'

    version_id = fields.Many2one('qdodoo.promotion.version',u'版本')
    name = fields.Char(u'条目名称',required=True)
    section_id = fields.Many2one('crm.case.section',u'品牌')
    category_id = fields.Many2one('product.category',u'品类')
    product_id = fields.Many2one('product.product',u'单品')
    product_items = fields.Many2one('product.product',u'服务类产品',required=True)
    all_money = fields.Float(u'满')
    active = fields.Boolean(u'有效')
    subtract_money = fields.Float(u'减')

    _defaults = {
        'active':True,
    }

class qdodoo_promotion_version_gift_items(models.Model):
    """
        满赠促销明细
    """
    _name = 'qdodoo.promotion.version.gift.items'

    version_id = fields.Many2one('qdodoo.promotion.version.gift',u'版本')
    name = fields.Char(u'条目名称',required=True)
    section_id = fields.Many2one('crm.case.section',u'品牌')
    product_id = fields.Many2one('product.product',u'单品',required=True)
    product_items = fields.Many2one('product.product',u'赠品',required=True)
    product_items_money = fields.Float(u'赠品金额')
    product_items_num = fields.Float(u'赠品数量')
    all_money = fields.Float(u'满')
    active = fields.Boolean(u'有效')
    subtract_money = fields.Float(u'赠')

    _defaults = {
        'active':True,
    }

class qdodoo_promotion_version_discount_items(models.Model):
    """
        打折促销明细
    """
    _name = 'qdodoo.promotion.version.discount.items'

    version_id = fields.Many2one('qdodoo.promotion.version.discount',u'版本')
    name = fields.Char(u'条目名称',required=True)
    section_id = fields.Many2one('crm.case.section',u'品牌')
    product_items = fields.One2many('qdodoo.promotion.version.discount.product','discount_id',u'单品')
    product_items_num = fields.Float(u'打折比例(%)',default="100")
    active = fields.Boolean(u'有效', default=True)

class qdodoo_user_promotion(models.Model):
    _name = 'qdodoo.user.promotion'
    _rec_name = 'promotion'

    user = fields.Many2one('res.users',u'用户')
    promotion = fields.Many2one('qdodoo.promotion',u'优惠活动')
    active = fields.Boolean(u'有效')

    _defaults = {
        'active':True
    }

class qdodoo_checking_list(models.Model):
    _name = 'qdodoo.checking.list'
    _order = 'id desc'

    date = fields.Datetime(u'操作时间')
    user_id = fields.Many2one('res.partner',u'用户')
    recharge = fields.Float(u'充值')
    comsume = fields.Float(u'消费')
    refund = fields.Float(u'订单退款')
    all_money = fields.Float(u'可用余额')
    type = fields.Selection([('beforehand',u'预存款'),('order',u'订货消费'),('refund',u'退款')],u'业务类型')
    notes = fields.Text(u'备注')

class qdodoo_promotion_version_discount_product(models.Model):
    """
        促销方案明细单品数据
    """
    _name = 'qdodoo.promotion.version.discount.product'

    discount_id = fields.Many2one('qdodoo.promotion.version.discount.items',u'促销明细')
    name = fields.Many2one('product.product',u'单品')
    all_num = fields.Float(u'总优惠数')
    order_num = fields.Float(u'订单优惠数')
