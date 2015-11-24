# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_purchase_order_sms_adger(models.Model):
    _inherit = 'purchase.order'
    _description = 'purchase.order_inherit'
    """
    采购订单继承，增加短信发送功能
    """

    @api.multi
    def sms_send_adger(self):
        content = self.env["ir.config_parameter"].get_param("purchase.sms.template")
        rs_send_service = self.env['rainsoft.sendsms']
        record_obj = self.env['sms.sending.records']
        phone_number = self.partner_id.mobile or self.partner_id.phone or None
        if not content:
            raise except_orm(_(u'警告'), _(u'短信模板未设置'))
        if phone_number:
            messages = content % self.partner_id.name
            res = rs_send_service.send(phone_number, messages)
            if res:
                if res['message'] == 'ok':
                    record_obj.create({
                        'partner_id': self.partner_id.id,
                        'phone_number': phone_number,
                        'body': content,
                        'date_time': fields.Datetime.now(),
                        'user_id': self.env.uid,
                        'record_source': 'purchase'
                    })
            else:
                raise except_orm(_(u'错误'), _(u'短信发送失败'))
        else:
            raise except_orm(_(u'警告'), _(u'供应商%s号码为空') % self.partner_id.name)


class qdodoo_sale_order_sms_adger(models.Model):
    _inherit = 'sale.order'
    _description = 'sale.order_inherit'
    """
    销售订单继承，增加短信发送功能
    """

    @api.multi
    def sms_send_adger(self):
        content = self.env["ir.config_parameter"].get_param("sale.sms.template")
        rs_send_service = self.env['rainsoft.sendsms']
        record_obj = self.env['sms.sending.records']
        phone_number = self.partner_id.mobile or self.partner_id.phone or None
        if not content:
            raise except_orm(_(u'警告'), _(u'短信模板未设置'))
        if phone_number:
            messages = content % self.partner_id.name
            res = rs_send_service.send(phone_number, messages)
            if res:
                if res['message'] == 'ok':
                    record_obj.create({
                        'partner_id': self.partner_id.id,
                        'phone_number': phone_number,
                        'body': content,
                        'date_time': fields.Datetime.now(),
                        'user_id': self.user_id.id,
                        'record_source': 'sale'
                    })
            else:
                raise except_orm(_(u'错误'), _(u'短信发送失败'))
        else:
            raise except_orm(_(u'警告'), _(u'供应商%s号码为空') % self.partner_id.name)


class qdodoo_purchase_order_sms_template(models.Model):
    _name = 'qdodoo.purchase.order.sms.template'
    _inherit = 'res.config.settings'
    _description = 'qdodoo.purchase.order.sms.template'

    """
    采购订单短信模板
    """

    def _get_sms_template(self):
        return u'暂无'

    purchase_sms_template = fields.Text(string=u'模板', required=True, default=_get_sms_template)

    @api.multi
    def get_default_val(self):
        purchase_sms_template = self.env['ir.config_parameter'].get_param('purchase.sms.template')

        res = {"purchase_sms_template": purchase_sms_template}
        return res

    @api.multi
    def set_default_val(self):
        config_parameters = self.env['ir.config_parameter']
        for record in self.browse(self.ids):
            config_parameters.set_param('purchase.sms.template', record.purchase_sms_template)

    @api.model
    def default_get(self, fields):
        res = super(qdodoo_purchase_order_sms_template, self).default_get(fields)
        return res


class qdodoo_sale_order_sms_template(models.Model):
    _name = 'qdodoo.sale.order.sms.template'
    _inherit = 'res.config.settings'
    _description = 'qdodoo.sale.order.sms.template'

    """
    销售订单短信模板
    """

    def _get_sms_template(self):
        return u'暂无'

    sale_sms_template = fields.Text(string=u'模板', required=True, default=_get_sms_template)

    @api.multi
    def get_default_val(self):
        sale_sms_template = self.env['ir.config_parameter'].get_param('sale.sms.template')

        res = {"sale_sms_template": sale_sms_template}
        return res

    @api.multi
    def set_default_val(self):
        config_parameters = self.env['ir.config_parameter']
        for record in self.browse(self.ids):
            config_parameters.set_param('sale.sms.template', record.sale_sms_template)

    @api.model
    def default_get(self, fields):
        res = super(qdodoo_sale_order_sms_template, self).default_get(fields)
        return res


class sms_sending_records(models.Model):
    _name = 'sms.sending.records'
    _description = 'sms.sending.records'
    """
    短信发送记录
    """
    partner_id = fields.Many2one('res.partner', string=u'供应商/客户')
    phone_number = fields.Char(string=u'电话号码')
    body = fields.Char(string=u'短信内容')
    date_time = fields.Datetime(string=u'发送时间')
    user_id = fields.Many2one('res.users', string=u'发送人')
    record_source = fields.Selection((('purchase', u'采购'), ('sale', u'销售')), string=u'记录来源')
