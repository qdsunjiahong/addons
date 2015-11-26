# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_sms_create_contract(models.Model):
    _inherit = 'account.analytic.account'

    order_manager_id = fields.Many2one('res.users', string=u'订单负责人', copy=False)
    sms_create = fields.Boolean(string=u'创建时发送短信', default=True)

    @api.model
    def create(self, vals):
        if vals.get('sms_create') == True:
            user_obj = self.env['res.users']
            content = self.env["ir.config_parameter"].get_param("contract.sms.template")
            partner_id = vals.get('partner_id', False)
            if partner_id:
                partner_name = self.env['res.partner'].browse(partner_id).name
            else:
                partner_name = "XX"
            if not content:
                raise except_orm(_(u'警告'), _(u'短信模板未设置'))

            message = content % (partner_name, fields.Date.today(), vals.get('name', u'XX合同'), vals.get('code', '**'))
            order_manager_id = vals.get('order_manager_id', False)
            if not order_manager_id:
                raise except_orm(_(u'警告'), _(u'订单负责人为空'))
            user_id = user_obj.browse(order_manager_id)
            phone_number = user_id.phone or user_id.mobile or None
            if not phone_number:
                raise except_orm(_(u'警告'), _(u'订单负责人电话或者手机未填写'))
            rs_send_service = self.env['rainsoft.sendsms']
            res = rs_send_service.send(phone_number, message)
            if res:
                if res['message'] == 'ok':
                    record_obj = self.env['sms.sending.records']
                    record_obj.create({
                        'partner_id': partner_id,
                        'phone_number': phone_number,
                        'body': message,
                        'date_time': fields.Datetime.now(),
                        'user_id': self.env.uid,
                        'record_source': u'新增合同'
                    })
                    return super(qdodoo_sms_create_contract, self).create(vals)
                else:
                    raise except_orm(_(u'警告'), _(u'短信发送失败'))
            else:
                raise except_orm(_(u'警告'), _(u'短信发送失败'))
        else:
            return super(qdodoo_sms_create_contract, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('order_manager_id', False):
            if self.sms_create == True or vals.get('sms_create', False) == True:
                user_obj = self.env['res.users']
                content = self.env["ir.config_parameter"].get_param("contract.sms.template")
                partner_id = vals.get('partner_id', False) or self.partner_id.id
                if partner_id:
                    partner_name = self.env['res.partner'].browse(partner_id).name
                else:
                    partner_name = "XX"
                if not content:
                    raise except_orm(_(u'警告'), _(u'短信模板未设置'))

                message = content % (
                    partner_name, fields.Date.today(), vals.get('name', '') or self.name or u"XX合同",
                    vals.get('code', '') or self.code) or "**"
                order_manager_id = vals.get('order_manager_id', False)
                if not order_manager_id:
                    raise except_orm(_(u'警告'), _(u'订单负责人为空'))
                user_id = user_obj.browse(order_manager_id)
                phone_number = user_id.phone or user_id.mobile or None
                if not phone_number:
                    raise except_orm(_(u'警告'), _(u'订单负责人电话或者手机未填写'))
                rs_send_service = self.env['rainsoft.sendsms']
                res = rs_send_service.send(phone_number, message)
                if res:
                    if res['message'] == 'ok':
                        record_obj = self.env['sms.sending.records']
                        record_obj.create({
                            'partner_id': partner_id,
                            'phone_number': phone_number,
                            'body': message,
                            'date_time': fields.Datetime.now(),
                            'user_id': self.env.uid,
                            'record_source': u'新增合同'
                        })
                        return super(qdodoo_sms_create_contract, self).write(vals)
                    else:
                        raise except_orm(_(u'警告'), _(u'短信发送失败'))
                else:
                    raise except_orm(_(u'警告'), _(u'短信发送失败'))
            else:
                return super(qdodoo_sms_create_contract, self).write(vals)


class qdodoo_contract_order_sms_template(models.Model):
    _name = 'qdodoo.contract.order.sms.template'
    _inherit = 'res.config.settings'

    """
    合同新建发送短信
    """

    contract_sms_template = fields.Text(string=u'模板', required=True)

    @api.multi
    def get_default_val(self):
        contract_sms_template = self.env['ir.config_parameter'].get_param('contract.sms.template')

        res = {"contract_sms_template": contract_sms_template}
        return res

    @api.multi
    def set_default_val(self):
        config_parameters = self.env['ir.config_parameter']
        for record in self.browse(self.ids):
            config_parameters.set_param('contract.sms.template', record.contract_sms_template)

    @api.model
    def default_get(self, fields):
        res = super(qdodoo_contract_order_sms_template, self).default_get(fields)
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
    record_source = fields.Char(string=u'记录来源')
