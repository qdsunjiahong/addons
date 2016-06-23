# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
import calendar
from openerp import tools
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_promotion(models.Model):
    """
        促销单
    """
    _name = 'qdodoo.promotion'    # 模型名称
    _description = 'qdodoo.promotion'    # 模型描述

    name = fields.Char(u'方案名称',required=True)
    selection_ids = fields.Selection([('reduction',u'满减促销'),('gift',u'满赠促销'),('discount',u'打折促销'),('deduction',u'减价促销')],u'促销类型')
    version_gift_id = fields.One2many('qdodoo.promotion.version.gift','promotion_id',string=u'方案版本')
    version_id = fields.One2many('qdodoo.promotion.version','promotion_id',string=u'方案版本')
    version_discount_id = fields.One2many('qdodoo.promotion.version.discount','promotion_id',string=u'方案版本')
    version_deduction_id = fields.One2many('qdodoo.promotion.version.deduction','promotion_id',string=u'方案版本')
    active = fields.Boolean(u'有效', default=True)
    company_id = fields.Many2one('res.company',u'公司',required=True)
    is_play = fields.Boolean(u'是否让客户自己报名', default=True)
    active_information = fields.Text(u'活动详情')

    _defaults = {
        'company_id': lambda self, cr, uid, ids, context=None:self.pool.get('res.users').browse(cr, uid, uid).company_id.id
    }

    @api.multi
    def write(self, vals):
        if vals.get('active'):
            self.env['qdodoo.is.promotion'].search([('promotion_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion, self).write(vals)

    @api.multi
    def unlink(self):
        self.env['qdodoo.is.promotion'].search([('promotion_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion, self).unlink()

class qdodoo_is_promotion(models.Model):
    """
        记录已经存在的促销规则
    """
    _name = 'qdodoo.is.promotion'

    name = fields.Many2one('product.product',u'产品')
    section_id = fields.Many2one('crm.case.section',u'销售团队')
    promotion_name = fields.Char(u'位置')
    date_start = fields.Date(u'开始日期')
    date_end = fields.Date(u'结束日期')
    version_gift_id = fields.Many2one('qdodoo.promotion.version.gift',string=u'方案版本')
    version_id = fields.Many2one('qdodoo.promotion.version',string=u'方案版本')
    version_discount_id = fields.Many2one('qdodoo.promotion.version.discount',string=u'方案版本')
    version_deduction_id = fields.Many2one('qdodoo.promotion.version.deduction',string=u'方案版本')
    promotion_id = fields.Many2one('qdodoo.promotion',u'促销单')

class qdodoo_promotion_version_gift(models.Model):
    """
        满赠促销版本
    """
    _name = 'qdodoo.promotion.version.gift'

    promotion_id = fields.Many2one('qdodoo.promotion',u'促销单')
    name = fields.Char(u'版本名称',required=True)
    date_start = fields.Date(u'开始时间')
    date_end = fields.Date(u'结束时间')
    active = fields.Boolean(u'有效', default=True)
    items_id = fields.One2many('qdodoo.promotion.version.gift.items','version_id',u'优惠条目')

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

    @api.multi
    def write(self, vals):
        if vals.get('active'):
            self.env['qdodoo.is.promotion'].search([('version_gift_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion_version_gift, self).write(vals)

    @api.multi
    def unlink(self):
        self.env['qdodoo.is.promotion'].search([('version_gift_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion_version_gift, self).unlink()

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

    @api.multi
    def write(self, vals):
        if vals.get('active'):
            self.env['qdodoo.is.promotion'].search([('version_discount_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion_version_discount, self).write(vals)

    @api.multi
    def unlink(self):
        self.env['qdodoo.is.promotion'].search([('version_discount_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion_version_discount, self).unlink()

class qdodoo_promotion_version_deduction(models.Model):
    """
        减价促销版本
    """
    _name = 'qdodoo.promotion.version.deduction'

    promotion_id = fields.Many2one('qdodoo.promotion',u'促销单')
    name = fields.Char(u'版本名称',required=True)
    date_start = fields.Date(u'开始时间')
    date_end = fields.Date(u'结束时间')
    active = fields.Boolean(u'有效', default=True)
    items_id = fields.One2many('qdodoo.promotion.version.deduction.items','version_id',u'优惠条目')

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
        return super(qdodoo_promotion_version_deduction, self).create(cr, uid, valus, context=context)

    @api.multi
    def write(self, vals):
        if vals.get('active'):
            self.env['qdodoo.is.promotion'].search([('version_deduction_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion_version_deduction, self).write(vals)

    @api.multi
    def unlink(self):
        self.env['qdodoo.is.promotion'].search([('version_deduction_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion_version_deduction, self).unlink()

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

    @api.multi
    def write(self, vals):
        if vals.get('active'):
            self.env['qdodoo.is.promotion'].search([('version_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion_version, self).write(vals)

    @api.multi
    def unlink(self):
        self.env['qdodoo.is.promotion'].search([('version_id','in',self.ids)]).unlink()
        return super(qdodoo_promotion_version, self).unlink()

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
    active = fields.Boolean(u'有效', default=True)
    subtract_money = fields.Float(u'减')
    analytic_1 = fields.Many2one('account.analytic.account',u'大区')
    analytic_2 = fields.Many2one('account.analytic.account',u'分公司')
    analytic_3 = fields.Many2one('account.analytic.account',u'城市')
    partner_id = fields.Many2one('res.users',u'单店')

    @api.model
    def create(self, vals):
        res = super(qdodoo_promotion_version_items, self).create(vals)
        product_obj = self.env['product.product']
        section_obj = self.env['crm.case.section']
        promotion_obj = self.env['qdodoo.is.promotion']
        domain = []
        if res.version_id.date_start and not res.version_id.date_end:
            domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',res.version_id.date_start),('date_end','>=',res.version_id.date_start))
        if res.version_id.date_end and not res.version_id.date_start:
            domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',res.version_id.date_end),('date_start','<=',res.version_id.date_end))
        if res.version_id.date_end and res.version_id.date_start:
            domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',res.version_id.date_end),'&',('date_start','=',False),('date_end','>=',res.version_id.date_start),'&',('date_start','>=',res.version_id.date_start),('date_start','<',res.version_id.date_end),'&',('date_end','<=',res.version_id.date_end),('date_end','>=',res.version_id.date_start),'&',('date_end','>=',res.version_id.date_end),('date_start','<=',res.version_id.date_start))
        # 获取所有的品牌
        if res.section_id:
            section_list = [res.section_id.id]
        else:
            section_list = section_obj.search([]).ids
        if res.product_id:
            product_list = [res.product_id.id]
        else:
            if res.category_id:
                product_list = product_obj.search([('categ_id','=',res.category_id.id),('company_id','=',res.version_id.promotion_id.company_id.id)]).ids
            else:
                product_list = product_obj.search([('company_id','=',res.version_id.promotion_id.company_id.id)]).ids
        domain.append(('name','in',product_list))
        domain.append(('section_id','in',section_list))
        promotion_ids = promotion_obj.search(domain)
        if promotion_ids:
            raise osv.except_osv(_(u'错误'),_(u'产品%s-销售团队%s已存在于%s中，请检查相关设置')%(promotion_ids[0].name.name,promotion_ids[0].section_id.name,promotion_ids[0].promotion_name))
        else:
            for product_l in product_list:
                for section_l in section_list:
                    promotion_obj.create({'promotion_id':res.version_id.promotion_id.id,'version_id':res.version_id.id,'name':product_l,'section_id':section_l,'date_start':res.version_id.date_start,
                                          'date_end':res.version_id.date_end,'promotion_name':'促销单'+res.version_id.promotion_id.name+'->版本'+res.version_id.name+'->条目'+res.name})
        return res

    @api.multi
    def write(self, vals):
        section_id_old = self.section_id
        product_id_old = self.product_id
        category_id_old = self.category_id
        super(qdodoo_promotion_version_items, self).write(vals)
        if vals.get('section_id') or vals.get('category_id') or vals.get('product_id'):
            product_obj = self.env['product.product']
            section_obj = self.env['crm.case.section']
            promotion_obj = self.env['qdodoo.is.promotion']
            domain = []
            if self.version_id.date_start and not self.version_id.date_end:
                domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',self.version_id.date_start),('date_end','>=',self.version_id.date_start))
            if self.version_id.date_end and not self.version_id.date_start:
                domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',self.version_id.date_end),('date_start','<=',self.version_id.date_end))
            if self.version_id.date_end and self.version_id.date_start:
                domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',self.version_id.date_end),'&',('date_start','=',False),('date_end','>=',self.version_id.date_start),'&',('date_start','>=',self.version_id.date_start),('date_start','<',self.version_id.date_end),'&',('date_end','<=',self.version_id.date_end),('date_end','>=',self.version_id.date_start),'&',('date_end','>=',self.version_id.date_end),('date_start','<=',self.version_id.date_start))
            # 获取所有的品牌
            if section_id_old:
                section_list = [section_id_old.id]
            else:
                section_list = section_obj.search([]).ids
            if product_id_old:
                product_list = [product_id_old.id]
            else:
                if category_id_old:
                    product_list = product_obj.search([('categ_id','=',category_id_old.id),('company_id','=',self.version_id.promotion_id.company_id.id)]).ids
                else:
                    product_list = product_obj.search([('company_id','=',self.version_id.promotion_id.company_id.id)]).ids
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            promotion_ids.unlink()

            # 获取所有的品牌
            if self.section_id:
                section_list = [self.section_id.id]
            else:
                section_list = section_obj.search([]).ids
            if self.product_id:
                product_list = [self.product_id.id]
            else:
                if self.category_id:
                    product_list = product_obj.search([('categ_id','=',self.category_id.id),('company_id','=',self.version_id.promotion_id.company_id.id)]).ids
                else:
                    product_list = product_obj.search([('company_id','=',self.version_id.promotion_id.company_id.id)]).ids
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            if promotion_ids:
                raise osv.except_osv(_(u'错误'),_(u'产品%s-销售团队%s已存在于%s中，请检查相关设置')%(promotion_ids[0].name.name,promotion_ids[0].section_id.name,promotion_ids[0].promotion_name))
            else:
                for product_l in product_list:
                    for section_l in section_list:
                        promotion_obj.create({'promotion_id':self.version_id.promotion_id.id,'version_id':self.version_id.id,'name':product_l,'section_id':section_l,'date_start':self.version_id.date_start,
                                              'date_end':self.version_id.date_end,'promotion_name':'促销单'+self.version_id.promotion_id.name+'->版本'+self.version_id.name+'->条目'+self.name})
        return True

    @api.multi
    def unlink(self):
        for line in self:
            product_obj = self.env['product.product']
            section_obj = self.env['crm.case.section']
            promotion_obj = self.env['qdodoo.is.promotion']
            domain = []
            if line.version_id.date_start and not line.version_id.date_end:
                domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',line.version_id.date_start),('date_end','>=',line.version_id.date_start))
            if line.version_id.date_end and not line.version_id.date_start:
                domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',line.version_id.date_end),('date_start','<=',line.version_id.date_end))
            if line.version_id.date_end and line.version_id.date_start:
                domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',line.version_id.date_end),'&',('date_start','=',False),('date_end','>=',line.version_id.date_start),'&',('date_start','>=',line.version_id.date_start),('date_start','<',line.version_id.date_end),'&',('date_end','<=',line.version_id.date_end),('date_end','>=',line.version_id.date_start),'&',('date_end','>=',line.version_id.date_end),('date_start','<=',line.version_id.date_start))
            # 获取所有的品牌
            if line.section_id:
                section_list = [line.section_id.id]
            else:
                section_list = section_obj.search([]).ids
            if line.product_id:
                product_list = [line.product_id.id]
            else:
                if line.category_id:
                    product_list = product_obj.search([('categ_id','=',line.category_id.id),('company_id','=',line.version_id.promotion_id.company_id.id)]).ids
                else:
                    product_list = product_obj.search([('company_id','=',line.version_id.promotion_id.company_id.id)]).ids
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            promotion_ids.unlink()
        return super(qdodoo_promotion_version_items, self).unlink()

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
    active = fields.Boolean(u'有效', default=True)
    subtract_money = fields.Float(u'赠')
    analytic_1 = fields.Many2one('account.analytic.account',u'大区')
    analytic_2 = fields.Many2one('account.analytic.account',u'分公司')
    analytic_3 = fields.Many2one('account.analytic.account',u'城市')
    partner_id = fields.Many2one('res.users',u'单店')

    @api.model
    def create(self, vals):
        res = super(qdodoo_promotion_version_gift_items, self).create(vals)
        section_obj = self.env['crm.case.section']
        promotion_obj = self.env['qdodoo.is.promotion']
        domain = []
        if res.version_id.date_start and not res.version_id.date_end:
            domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',res.version_id.date_start),('date_end','>=',res.version_id.date_start))
        if res.version_id.date_end and not res.version_id.date_start:
            domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',res.version_id.date_end),('date_start','<=',res.version_id.date_end))
        if res.version_id.date_end and res.version_id.date_start:
            domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',res.version_id.date_end),'&',('date_start','=',False),('date_end','>=',res.version_id.date_start),'&',('date_start','>=',res.version_id.date_start),('date_start','<',res.version_id.date_end),'&',('date_end','<=',res.version_id.date_end),('date_end','>=',res.version_id.date_start),'&',('date_end','>=',res.version_id.date_end),('date_start','<=',res.version_id.date_start))
        # 获取所有的品牌
        if res.section_id:
            section_list = [res.section_id.id]
        else:
            section_list = section_obj.search([]).ids
        product_list = [res.product_id.id]
        domain.append(('name','in',product_list))
        domain.append(('section_id','in',section_list))
        promotion_ids = promotion_obj.search(domain)
        if promotion_ids:
            raise osv.except_osv(_(u'错误'),_(u'产品%s-销售团队%s已存在于%s中，请检查相关设置')%(promotion_ids[0].name.name,promotion_ids[0].section_id.name,promotion_ids[0].promotion_name))
        else:
            for product_l in product_list:
                for section_l in section_list:
                    promotion_obj.create({'promotion_id':res.version_id.promotion_id.id,'version_gift_id':res.version_id.id,'name':product_l,'section_id':section_l,'date_start':res.version_id.date_start,
                                          'date_end':res.version_id.date_end,'promotion_name':'促销单'+res.version_id.promotion_id.name+'->版本'+res.version_id.name+'->条目'+res.name})
        return res

    @api.multi
    def write(self, vals):
        section_id_old = self.section_id
        product_id_old = self.product_id
        super(qdodoo_promotion_version_gift_items, self).write(vals)
        if vals.get('section_id') or vals.get('category_id') or vals.get('product_id'):
            section_obj = self.env['crm.case.section']
            promotion_obj = self.env['qdodoo.is.promotion']
            domain = []
            if self.version_id.date_start and not self.version_id.date_end:
                domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',self.version_id.date_start),('date_end','>=',self.version_id.date_start))
            if self.version_id.date_end and not self.version_id.date_start:
                domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',self.version_id.date_end),('date_start','<=',self.version_id.date_end))
            if self.version_id.date_end and self.version_id.date_start:
                domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',self.version_id.date_end),'&',('date_start','=',False),('date_end','>=',self.version_id.date_start),'&',('date_start','>=',self.version_id.date_start),('date_start','<',self.version_id.date_end),'&',('date_end','<=',self.version_id.date_end),('date_end','>=',self.version_id.date_start),'&',('date_end','>=',self.version_id.date_end),('date_start','<=',self.version_id.date_start))
            # 获取所有的品牌
            if section_id_old:
                section_list = [section_id_old.id]
            else:
                section_list = section_obj.search([]).ids
            product_list = [product_id_old.id]
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            promotion_ids.unlink()

            # 获取所有的品牌
            if self.section_id:
                section_list = [self.section_id.id]
            else:
                section_list = section_obj.search([]).ids
            product_list = [self.product_id.id]
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            if promotion_ids:
                raise osv.except_osv(_(u'错误'),_(u'产品%s-销售团队%s已存在于%s中，请检查相关设置')%(promotion_ids[0].name.name,promotion_ids[0].section_id.name,promotion_ids[0].promotion_name))
            else:
                for product_l in product_list:
                    for section_l in section_list:
                        promotion_obj.create({'promotion_id':self.version_id.promotion_id.id,'version_gift_id':self.version_id.id,'name':product_l,'section_id':section_l,'date_start':self.version_id.date_start,
                                              'date_end':self.version_id.date_end,'promotion_name':'促销单'+self.version_id.promotion_id.name+'->版本'+self.version_id.name+'->条目'+self.name})
        return True

    @api.multi
    def unlink(self):
        for line in self:
            product_obj = self.env['product.product']
            section_obj = self.env['crm.case.section']
            promotion_obj = self.env['qdodoo.is.promotion']
            domain = []
            if line.version_id.date_start and not line.version_id.date_end:
                domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',line.version_id.date_start),('date_end','>=',line.version_id.date_start))
            if line.version_id.date_end and not line.version_id.date_start:
                domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',line.version_id.date_end),('date_start','<=',line.version_id.date_end))
            if line.version_id.date_end and line.version_id.date_start:
                domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',line.version_id.date_end),'&',('date_start','=',False),('date_end','>=',line.version_id.date_start),'&',('date_start','>=',line.version_id.date_start),('date_start','<',line.version_id.date_end),'&',('date_end','<=',line.version_id.date_end),('date_end','>=',line.version_id.date_start),'&',('date_end','>=',line.version_id.date_end),('date_start','<=',line.version_id.date_start))
            # 获取所有的品牌
            if line.section_id:
                section_list = [line.section_id.id]
            else:
                section_list = section_obj.search([]).ids
            product_list = [line.product_id.id]
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            promotion_ids.unlink()
        return super(qdodoo_promotion_version_gift_items, self).unlink()

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
    analytic_1 = fields.Many2one('account.analytic.account',u'大区')
    analytic_2 = fields.Many2one('account.analytic.account',u'分公司')
    analytic_3 = fields.Many2one('account.analytic.account',u'城市')
    partner_id = fields.Many2one('res.users',u'单店')

    @api.model
    def create(self, vals):
        res = super(qdodoo_promotion_version_discount_items, self).create(vals)
        section_obj = self.env['crm.case.section']
        promotion_obj = self.env['qdodoo.is.promotion']
        domain = []
        if res.version_id.date_start and not res.version_id.date_end:
            domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',res.version_id.date_start),('date_end','>=',res.version_id.date_start))
        if res.version_id.date_end and not res.version_id.date_start:
            domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',res.version_id.date_end),('date_start','<=',res.version_id.date_end))
        if res.version_id.date_end and res.version_id.date_start:
            domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',res.version_id.date_end),'&',('date_start','=',False),('date_end','>=',res.version_id.date_start),'&',('date_start','>=',res.version_id.date_start),('date_start','<',res.version_id.date_end),'&',('date_end','<=',res.version_id.date_end),('date_end','>=',res.version_id.date_start),'&',('date_end','>=',res.version_id.date_end),('date_start','<=',res.version_id.date_start))
        # 获取所有的品牌
        if res.section_id:
            section_list = [res.section_id.id]
        else:
            section_list = section_obj.search([]).ids
        product_list = []
        for product_item in res.product_items:
            product_list.append(product_item.name.id)
        domain.append(('name','in',product_list))
        domain.append(('section_id','in',section_list))
        promotion_ids = promotion_obj.search(domain)
        if promotion_ids:
            raise osv.except_osv(_(u'错误'),_(u'产品%s-销售团队%s已存在于%s中，请检查相关设置')%(promotion_ids[0].name.name,promotion_ids[0].section_id.name,promotion_ids[0].promotion_name))
        else:
            for product_l in product_list:
                for section_l in section_list:
                    promotion_obj.create({'promotion_id':res.version_id.promotion_id.id,'version_discount_id':res.version_id.id,'name':product_l,'section_id':section_l,'date_start':res.version_id.date_start,
                                          'date_end':res.version_id.date_end,'promotion_name':'促销单'+res.version_id.promotion_id.name+'->版本'+res.version_id.name+'->条目'+res.name})
        return res

    @api.multi
    def write(self, vals):
        section_id_old = self.section_id
        product_items_old = self.product_items
        super(qdodoo_promotion_version_discount_items, self).write(vals)
        if vals.get('section_id') or vals.get('category_id') or vals.get('product_items'):
            section_obj = self.env['crm.case.section']
            promotion_obj = self.env['qdodoo.is.promotion']
            domain = []
            if self.version_id.date_start and not self.version_id.date_end:
                domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',self.version_id.date_start),('date_end','>=',self.version_id.date_start))
            if self.version_id.date_end and not self.version_id.date_start:
                domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',self.version_id.date_end),('date_start','<=',self.version_id.date_end))
            if self.version_id.date_end and self.version_id.date_start:
                domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',self.version_id.date_end),'&',('date_start','=',False),('date_end','>=',self.version_id.date_start),'&',('date_start','>=',self.version_id.date_start),('date_start','<',self.version_id.date_end),'&',('date_end','<=',self.version_id.date_end),('date_end','>=',self.version_id.date_start),'&',('date_end','>=',self.version_id.date_end),('date_start','<=',self.version_id.date_start))
            # 获取所有的品牌
            if section_id_old:
                section_list = [section_id_old.id]
            else:
                section_list = section_obj.search([]).ids
            product_list = []
            for product_item in product_items_old:
                product_list.append(product_item.name.id)
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            promotion_ids.unlink()

            # 获取所有的品牌
            if self.section_id:
                section_list = [self.section_id.id]
            else:
                section_list = section_obj.search([]).ids
            product_list = []
            for product_item in self.product_items:
                product_list.append(product_item.name.id)
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            if promotion_ids:
                raise osv.except_osv(_(u'错误'),_(u'产品%s-销售团队%s已存在于%s中，请检查相关设置')%(promotion_ids[0].name.name,promotion_ids[0].section_id.name,promotion_ids[0].promotion_name))
            else:
                for product_l in product_list:
                    for section_l in section_list:
                        promotion_obj.create({'promotion_id':self.version_id.promotion_id.id,'version_discount_id':self.version_id.id,'name':product_l,'section_id':section_l,'date_start':self.version_id.date_start,
                                              'date_end':self.version_id.date_end,'promotion_name':'促销单'+self.version_id.promotion_id.name+'->版本'+self.version_id.name+'->条目'+self.name})
        return True

    @api.multi
    def unlink(self):
        for line in self:
            section_obj = self.env['crm.case.section']
            promotion_obj = self.env['qdodoo.is.promotion']
            domain = []
            if line.version_id.date_start and not line.version_id.date_end:
                domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',line.version_id.date_start),('date_end','>=',line.version_id.date_start))
            if line.version_id.date_end and not line.version_id.date_start:
                domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',line.version_id.date_end),('date_start','<=',line.version_id.date_end))
            if line.version_id.date_end and line.version_id.date_start:
                domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',line.version_id.date_end),'&',('date_start','=',False),('date_end','>=',line.version_id.date_start),'&',('date_start','>=',line.version_id.date_start),('date_start','<',line.version_id.date_end),'&',('date_end','<=',line.version_id.date_end),('date_end','>=',line.version_id.date_start),'&',('date_end','>=',line.version_id.date_end),('date_start','<=',line.version_id.date_start))
            # 获取所有的品牌
            if line.section_id:
                section_list = [line.section_id.id]
            else:
                section_list = section_obj.search([]).ids
            product_list = []
            for product_item in line.product_items:
                product_list.append(product_item.name.id)
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            promotion_ids.unlink()
        return super(qdodoo_promotion_version_discount_items, self).unlink()

class qdodoo_promotion_version_deduction_items(models.Model):
    """
        打折促销明细
    """
    _name = 'qdodoo.promotion.version.deduction.items'

    version_id = fields.Many2one('qdodoo.promotion.version.deduction',u'版本')
    name = fields.Char(u'条目名称',required=True)
    section_id = fields.Many2one('crm.case.section',u'品牌')
    product_id = fields.Many2one('product.product',u'单品', required=True)
    product_items_num = fields.Float(u'减价金额')
    active = fields.Boolean(u'有效', default=True)
    analytic_1 = fields.Many2one('account.analytic.account',u'大区')
    analytic_2 = fields.Many2one('account.analytic.account',u'分公司')
    analytic_3 = fields.Many2one('account.analytic.account',u'城市')
    partner_id = fields.Many2one('res.users',u'单店')

    @api.model
    def create(self, vals):
        res = super(qdodoo_promotion_version_deduction_items, self).create(vals)
        section_obj = self.env['crm.case.section']
        promotion_obj = self.env['qdodoo.is.promotion']
        domain = []
        if res.version_id.date_start and not res.version_id.date_end:
            domain.append(('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',res.version_id.date_start),('date_end','>=',res.version_id.date_start)))
        if res.version_id.date_end and not res.version_id.date_start:
            domain.append(('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',res.version_id.date_end),('date_start','<=',res.version_id.date_end)))
        if res.version_id.date_end and res.version_id.date_start:
            domain.append(('|','|','|','|','&',('date_end','=',False),('date_start','<=',res.version_id.date_end),'&',('date_start','=',False),('date_end','>=',res.version_id.date_start),'&',('date_start','>=',res.version_id.date_start),('date_start','<',res.version_id.date_end),'&',('date_end','<=',res.version_id.date_end),('date_end','>=',res.version_id.date_start),'&',('date_end','>=',res.version_id.date_end),('date_start','<=',res.version_id.date_start)))
        # 获取所有的品牌
        if res.section_id:
            section_list = [res.section_id.id]
        else:
            section_list = section_obj.search([]).ids
        product_list = [self.product_id.id]
        domain.append(('name','in',product_list))
        domain.append(('section_id','in',section_list))
        promotion_ids = promotion_obj.search(domain)
        if promotion_ids:
            raise osv.except_osv(_(u'错误'),_(u'产品%s-销售团队%s已存在于%s中，请检查相关设置')%(promotion_ids[0].name.name,promotion_ids[0].section_id.name,promotion_ids[0].promotion_name))
        else:
            for product_l in product_list:
                for section_l in section_list:
                    promotion_obj.create({'promotion_id':res.version_id.promotion_id.id,'version_deduction_id':res.version_id.id,'name':product_l,'section_id':section_l,'date_start':res.version_id.date_start,
                                          'date_end':res.version_id.date_end,'promotion_name':'促销单'+res.version_id.promotion_id.name+'->版本'+res.version_id.name+'->条目'+res.name})
        return res

    @api.multi
    def write(self, vals):
        section_id_old = self.section_id
        product_id_old = self.product_id
        super(qdodoo_promotion_version_deduction_items, self).write(vals)
        if vals.get('section_id') or vals.get('product_id'):
            section_obj = self.env['crm.case.section']
            promotion_obj = self.env['qdodoo.is.promotion']
            domain = []
            if self.version_id.date_start and not self.version_id.date_end:
                domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',self.version_id.date_start),('date_end','>=',self.version_id.date_start))
            if self.version_id.date_end and not self.version_id.date_start:
                domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',self.version_id.date_end),('date_start','<=',self.version_id.date_end))
            if self.version_id.date_end and self.version_id.date_start:
                domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',self.version_id.date_end),'&',('date_start','=',False),('date_end','>=',self.version_id.date_start),'&',('date_start','>=',self.version_id.date_start),('date_start','<',self.version_id.date_end),'&',('date_end','<=',self.version_id.date_end),('date_end','>=',self.version_id.date_start),'&',('date_end','>=',self.version_id.date_end),('date_start','<=',self.version_id.date_start))
            # 获取所有的品牌
            if section_id_old:
                section_list = [section_id_old.id]
            else:
                section_list = section_obj.search([]).ids
            product_list = [product_id_old.id]
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            promotion_ids.unlink()
            # 获取所有的品牌
            if self.section_id:
                section_list = [self.section_id.id]
            else:
                section_list = section_obj.search([]).ids
            product_list = [self.product_id.id]
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            if promotion_ids:
                raise osv.except_osv(_(u'错误'),_(u'产品%s-销售团队%s已存在于%s中，请检查相关设置')%(promotion_ids[0].name.name,promotion_ids[0].section_id.name,promotion_ids[0].promotion_name))
            else:
                for product_l in product_list:
                    for section_l in section_list:
                        promotion_obj.create({'promotion_id':self.version_id.promotion_id.id,'version_deduction_id':self.version_id.id,'name':product_l,'section_id':section_l,'date_start':self.version_id.date_start,
                                              'date_end':self.version_id.date_end,'promotion_name':'促销单'+self.version_id.promotion_id.name+'->版本'+self.version_id.name+'->条目'+self.name})
        return True

    @api.multi
    def unlink(self):
        for line in self:
            section_obj = self.env['crm.case.section']
            promotion_obj = self.env['qdodoo.is.promotion']
            domain = []
            if line.version_id.date_start and not line.version_id.date_end:
                domain.append('|',('date_end','=',False),'&','|',('date_start','=',False),('date_start','<=',line.version_id.date_start),('date_end','>=',line.version_id.date_start))
            if line.version_id.date_end and not line.version_id.date_start:
                domain.append('|',('date_start','=',False),'&','|',('date_end','=',False),('date_end','>=',line.version_id.date_end),('date_start','<=',line.version_id.date_end))
            if line.version_id.date_end and line.version_id.date_start:
                domain.append('|','|','|','|','&',('date_end','=',False),('date_start','<=',line.version_id.date_end),'&',('date_start','=',False),('date_end','>=',line.version_id.date_start),'&',('date_start','>=',line.version_id.date_start),('date_start','<',line.version_id.date_end),'&',('date_end','<=',line.version_id.date_end),('date_end','>=',line.version_id.date_start),'&',('date_end','>=',line.version_id.date_end),('date_start','<=',line.version_id.date_start))
            # 获取所有的品牌
            if line.section_id:
                section_list = [line.section_id.id]
            else:
                section_list = section_obj.search([]).ids
            product_list = [line.product_id.id]
            domain.append(('name','in',product_list))
            domain.append(('section_id','in',section_list))
            promotion_ids = promotion_obj.search(domain)
            promotion_ids.unlink()
        return super(qdodoo_promotion_version_deduction_items, self).unlink()

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
    one_portal_num = fields.Float(u'单店总优惠数')

    @api.model
    def create(self, vals):
        res = super(qdodoo_promotion_version_discount_product, self).create(vals)
        portal_obj = self.env['qdodoo.one.portal.num']
        users_obj = self.env['res.users']
        if vals.get('one_portal_num'):
            domain = []
            # 根据品牌查询出满足条件的用户
            if res.discount_id.section_id:
                domain.append(('default_section_id','=',res.discount_id.section_id))
            users_ids = users_obj.search(domain)
            for users_id in users_ids:
                portal_obj.create({'name':res.name.id,'protal_id':users_id.id,'one_portal_num':vals.get('one_portal_num')})
        return res

    @api.multi
    def write(self, vals):
        super(qdodoo_promotion_version_discount_product, self).write(vals)
        portal_obj = self.env['qdodoo.one.portal.num']
        users_obj = self.env['res.users']
        if vals.get('one_portal_num'):
            domain = []
            # 根据品牌查询出满足条件的用户
            if self.discount_id.section_id:
                domain.append(('default_section_id','=',self.discount_id.section_id))
            users_ids = users_obj.search(domain)
            portal_obj_ids = portal_obj.search([('name','=',self.name.id),('protal_id','in',users_ids.ids)])
            portal_obj_ids.write({'one_portal_num':vals.get('one_portal_num')})
        return True

    @api.multi
    def unlink(self):
        for line in self:
            portal_obj = self.env['qdodoo.one.portal.num']
            users_obj = self.env['res.users']
            domain = []
            # 根据品牌查询出满足条件的用户
            if line.discount_id.section_id:
                domain.append(('default_section_id','=',line.discount_id.section_id))
            users_ids = users_obj.search(domain)
            portal_obj_ids = portal_obj.search([('name','=',line.name.id),('protal_id','in',users_ids.ids)])
            portal_obj_ids.unlink()
        return super(qdodoo_promotion_version_discount_product, self).unlink()

class qdodoo_one_portal_num(models.Model):
    """
        单个门店的总优惠数
    """
    _name = 'qdodoo.one.portal.num'

    name = fields.Many2one('product.product',u'产品')
    protal_id = fields.Many2one('res.users',u'门店')
    one_portal_num = fields.Float(u'可优惠数')

class qdodoo_account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self, vals):
        res = super(qdodoo_account_move_line, self).create(vals)
        if res.partner_id and res.account_id.type in ('receivable','payable'):
            recharge = 0
            comsume = 0
            if res.account_id.type == 'receivable':
                if res.debit:
                    comsume = res.debit
                    type = 'order'
                if res.credit:
                    recharge = res.credit
                    type = 'beforehand'
            if comsume or recharge:
                all_money = -res.partner_id.credit + recharge - comsume
                self.env['qdodoo.checking.list'].sudo().create({'date':datetime.now(),'user_id':res.partner_id.id,'recharge':recharge,'comsume':comsume,
                                                         'all_money':all_money,'type':type})
        return res

class qdodoo_order_max_wizard(models.Model):
    """
        秒杀资格
    """
    _name = 'qdodoo.order.max.wizard'

    name = fields.Many2one('res.partner',u'客户')
    date = fields.Date(u'日期')
    order_id = fields.Many2one('sale.order',u'订单')
    money = fields.Float(u'订单金额', )

    @api.multi
    def btn_search(self):
        ids = self.search([])
        ids.unlink()
        seckill_obj = self.env['qdodoo.order.seckill']
        now = datetime.now().strftime('%Y-%m-%d')
        state_date_old = now[:8] + '01'
        state_date = (datetime.strptime(state_date_old,'%Y-%m-%d') + timedelta(days=-1)).strftime('%Y-%m-%d') + ' 15:00:00'
        days = calendar.monthrange(int(now[:4]), int(now[5:7]))
        end_date = now[:8] + str(days[1]) + ' 15:59:59'
        order_obj = self.env['sale.order']
        order_ids = order_obj.search([('date_order','>=',state_date),('date_order','<=',end_date),('state','=','done')])
        info_dict = {} #业务伙伴：订单
        max = self.env['ir.config_parameter'].get_param('order.max')
        for order_id in order_ids:
            if order_id.amount_total >= float(max):
                if order_id.partner_id.id not in info_dict:
                    info_dict[order_id.partner_id.id] = order_id
        for key, value in info_dict.items():
            seckill_obj.create({'name':value.id})
        result = self.env['ir.model.data'].get_object_reference('qdodoo_websale_update', 'tree_qdodoo_order_seckill')
        view_id = result and result[1] or False
        return {
              'name': _('秒杀资格'),
              'view_type': 'form',
              "view_mode": 'tree',
              'res_model': 'qdodoo.order.seckill',
              'type': 'ir.actions.act_window',
              'views': [(view_id,'tree')],
              'view_id': [view_id],
              }

class qdodoo_order_seckill(models.Model):
    """
        秒杀资格
    """
    _name = 'qdodoo.order.seckill'

    name = fields.Many2one('sale.order',u'订单')
    partner_id = fields.Many2one('res.partner',u'客户', related='name.partner_id')
    date = fields.Datetime(u'日期', related='name.date_order')
    money = fields.Float(u'订单金额', related='name.amount_total')

# class qdodoo_res_users(models.Model):
#     """
#         用户增加门店标识
#     """
#     _inherit = 'res.users'

    # is_portal_partner = fields.Boolean(u'是门店')
    # city_id_new = fields.Many2one('account.analytic.account',u'城市')