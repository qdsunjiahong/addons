# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_car_archives(models.Model):
    """
        车辆档案
    """
    _name = 'qdodoo.car.archives'    # 模型名称

    name = fields.Char(u'车架号')
    car_sale_price = fields.Float(u'进口合同价')
    car_model = fields.Many2one('product.product',u'车型')
    import_pay_money = fields.Float(u'进口预付定金')
    purchase_type = fields.Selection([('agency_in',u'委托进口'),('own_in',u'自营进口'),('own',u'内贸自营采购')],u'采购渠道')
    credit_price = fields.Float(u'信用证价格')
    contract_id = fields.Many2one('qdodoo.car.in.contract',u'整车采购')
    agency_id = fields.Many2one('qdodoo.entrusted.agency',u'委托协议')
    import_number = fields.Many2one('qdodoo.car.in.contract.new',u'进口合同号')
    agent_margin_price = fields.Float(u'代理服务费金额')
    lading_number = fields.Many2one('qdodoo.car.bill.lading',u'收货通知单号')
    payment_id = fields.Many2one('payment.line',u'付款申请单')
    redeem_car = fields.Float(u'赎车金额')
    out_port = fields.Date(u'离港日期')
    settlement_price = fields.Float(u'结算金额')
    in_port = fields.Date(u'到港日期')
    import_cost = fields.Float(u'进口成本')
    redeem_apply_number = fields.Many2one('qdodoo.redeem.car',u'赎车申请单号')
    car_cif = fields.Float(u'车辆实际到岸价')
    # settlement_number = fields.Many2one('qdodoo.settlement.order',u'结算通知单号')
    is_log = fields.Boolean(u'是否已移库')
    is_log_two = fields.Boolean(u'是否已移库')
    location_id = fields.Many2one('stock.location',u'库位')
    is_sale = fields.Boolean(u'已销售')
    sale_order = fields.Many2one('sale.order',u'销售单号')

    @api.one
    @api.constrains('name')
    def _check_total_day(self):
        if self.name and len(self.name) != 17:
            raise ValidationError("车架号必须是17位！")
        return True

    _defaults = {
        'is_sale':False
    }

    _sql_constraints = [
        ('code_name', 'unique(name)', u'车架号违反唯一性约束!')
    ]

class qdodoo_car_type(models.Model):
    """
        产品类别
    """
    _name = 'qdodoo.car.type'    # 模型名称

    name = fields.Char(u'品类',required=True)
    description = fields.Text(u'注解')

# class qdodoo_product_brand(models.Model):
#     _name = 'qdodoo.product.brand'
#
#     name = fields.Char(u'品牌')
#
# class qdodoo_version(models.Model):
#     _name = 'qdodoo.version'
#
#     name = fields.Char(u'版本')
#     order_id = fields.Many2one('qdodoo.product.brand',u'品牌')
#
# class qdodoo_series_of(models.Model):
#     _name = 'qdodoo.series.of'
#
#     brand_id = fields.Many2one('qdodoo.product.brand',u'品牌')
#     order_id = fields.Many2one('qdodoo.version',u'版本')
#     name = fields.Char(u'系列')
#
# class qdodoo_product_year(models.Model):
#     _name = 'qdodoo.product.year'
#
#     brand_id = fields.Many2one('qdodoo.product.brand',u'品牌')
#     version_id = fields.Many2one('qdodoo.version',u'版本')
#     order_id = fields.Many2one('qdodoo.series.of',u'系列')
#     name = fields.Char(u'年款')
#
# class qdodoo_model(models.Model):
#     _name = 'qdodoo.model'
#
#     brand_id = fields.Many2one('qdodoo.product.brand',u'品牌')
#     version_id = fields.Many2one('qdodoo.version',u'版本')
#     series_id = fields.Many2one('qdodoo.series.of',u'系列')
#     order_id = fields.Many2one('qdodoo.product.year',u'年款')
#     name = fields.Char(u'型号')
#
# class qdodoo_appearance(models.Model):
#     _name = 'qdodoo.appearance'
#
#     brand_id = fields.Many2one('qdodoo.product.brand',u'品牌')
#     version_id = fields.Many2one('qdodoo.version',u'版本')
#     series_id = fields.Many2one('qdodoo.series.of',u'系列')
#     year_id = fields.Many2one('qdodoo.product.year',u'年款')
#     order_id = fields.Many2one('qdodoo.model',u'型号')
#     name = fields.Char(u'外观')
#
# class qdodoo_interior(models.Model):
#     _name = 'qdodoo.interior'
#
#     brand_id = fields.Many2one('qdodoo.product.brand',u'品牌')
#     version_id = fields.Many2one('qdodoo.version',u'版本')
#     series_id = fields.Many2one('qdodoo.series.of',u'系列')
#     year_id = fields.Many2one('qdodoo.product.year',u'年款')
#     model_id = fields.Many2one('qdodoo.model',u'型号')
#     order_id = fields.Many2one('qdodoo.appearance',u'外观')
#     name = fields.Char(u'内饰')
#
# class qdodoo_configuration(models.Model):
#     _name = 'qdodoo.configuration'
#
#     brand_id = fields.Many2one('qdodoo.product.brand',u'品牌')
#     version_id = fields.Many2one('qdodoo.version',u'版本')
#     series_id = fields.Many2one('qdodoo.series.of',u'系列')
#     year_id = fields.Many2one('qdodoo.product.year',u'年款')
#     model_id = fields.Many2one('qdodoo.model',u'型号')
#     appearance_id = fields.Many2one('qdodoo.appearance',u'外观')
#     order_id = fields.Many2one('qdodoo.interior',u'内饰')
#     name = fields.Char(u'配置')

class qdodoo_shipment_port(models.Model):
    """
        港口
    """
    _name = 'qdodoo.shipment.port'    # 模型名称

    name = fields.Char(u'港口',required=True)
    country_id = fields.Many2one('res.country',u'国家',required=True)
    type = fields.Selection([('out',u'目的港'),('in',u'发货港')],u'类型',required=True)

class qdodoo_contract_template(models.Model):
    """
        合同模板
    """
    _name = 'qdodoo.contract.template'    # 模型名称

    name = fields.Char(u'模板名称',required=True)
    # description = fields.Text(u'模板内容',required=True)
    partner_id = fields.Many2one('res.partner',u'业务伙伴',required=True)

class qdodoo_payment_type(models.Model):
    """
        付款方式
    """
    _name = 'qdodoo.payment.type'    # 模型名称

    name = fields.Char(u'付款方式',required=True)
    description = fields.Text(u'说明')

class qdodoo_payment_line(models.Model):
    """
        价格条款
    """
    _name = 'qdodoo.payment.line'    # 模型名称

    name = fields.Char(u'价格条款',required=True)
    description = fields.Text(u'说明')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: