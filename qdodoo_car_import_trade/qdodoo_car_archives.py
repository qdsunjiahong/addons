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
    car_sale_price = fields.Float(u'车辆出口价')
    car_model = fields.Many2one('product.product',u'车型')
    import_pay_money = fields.Float(u'进口预付定金')
    purchase_type = fields.Many2one('qdodoo.car.purchase.type',u'采购渠道')
    credit_price = fields.Float(u'信用证价格')
    contract_id = fields.Many2one('qdodoo.car.in.contract',u'进口合同')
    agency_id = fields.Many2one('qdodoo.entrusted.agency',u'委托协议')
    import_number = fields.Char(u'进口合同号')
    agent_margin_price = fields.Float(u'代理保证金金额')
    lading_number = fields.Many2one('qdodoo.car.bill.lading',u'提单号')
    payment_id = fields.Many2one('payment.line',u'付款通知单')
    redeem_car = fields.Float(u'赎车金额')
    out_port = fields.Date(u'离港日期')
    settlement_price = fields.Float(u'结算金额')
    in_port = fields.Date(u'到港日期')
    import_cost = fields.Float(u'进口成本')
    redeem_apply_number = fields.Many2one('qdodoo.redeem.car',u'赎车申请单号')
    car_cif = fields.Float(u'车辆实际到岸价')
    settlement_number = fields.Many2one('qdodoo.settlement.order',u'结算通知单号')

    @api.one
    @api.constrains('name')
    def _check_total_day(self):
        if self.name and len(self.name) != 17:
            raise ValidationError("车架号必须是17位！")
        return True

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

class qdodoo_car_purchase_type(models.Model):
    """
        采购渠道
    """
    _name = 'qdodoo.car.purchase.type'    # 模型名称

    name = fields.Char(u'品类',required=True)
    description = fields.Text(u'注解')

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
    description = fields.Text(u'模板内容',required=True)
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