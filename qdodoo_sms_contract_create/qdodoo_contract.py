# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
import datetime
import logging
_logger = logging.getLogger(__name__)

class qdodoo_sms_create_contract(models.Model):
    """
    继承会计辅助核算模块，并在视图上添加订单负责人和发送短信选项
    以新API形式重载create和write方法，根据新加的选项视情况发送短信
    然后调用父类方法继续处理
    """
    _inherit = 'account.analytic.account'

    order_manager_id = fields.Many2one('res.users', string=u'订单负责人', copy=False)
    sms_create = fields.Boolean(string=u'创建时发送短信', default=True)

    @api.model
    def create(self, vals):
        if vals.get('sms_create') == True:  #如果设置创建时即发送短信，则发送
            user_obj = self.env['res.users']
            content = self.env["ir.config_parameter"].get_param("contract.sms.template")
            partner_id = vals.get('partner_id', False)
            if partner_id:
                partner_name = self.env['res.partner'].browse(partner_id).name
            else:
                partner_name = "XX"
            if not content:
                raise except_orm(_(u'警告'), _(u'短信模板未设置'))

            message = '发个固定内容的短信'
            message = content % (partner_name, fields.Date.today(), vals.get('name', u'XX合同'), vals.get('code', '**'))

            #订单负责人ID
            order_manager_id = vals.get('order_manager_id', False)
            if not order_manager_id:
                raise except_orm(_(u'警告'), _(u'订单负责人为空'))

            #获取订单负责人手机号等信息
            user_id = user_obj.browse(order_manager_id)
            phone_number = user_id.phone or user_id.mobile or None
            if not phone_number:
                raise except_orm(_(u'警告'), _(u'订单负责人电话或者手机未填写'))

            #发送短信，并创建短信发送记录
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

                    #创建本Model记录
                    return super(qdodoo_sms_create_contract, self).create(vals)
                else:
                    raise except_orm(_(u'警告'), _(u'短信发送失败'))
            else:
                raise except_orm(_(u'警告'), _(u'短信发送失败'))
        else:  #如果不自动发送短信，则创建一条供货商信息，并记录短信发送记录
            supplise_obj = self.env['supplise.ex']
            if vals.get('partner_id'):
                supplise_id = supplise_obj.search([('company_id_new','=',vals.get('contract_compa;ny1')),('partner_id','=',vals.get('partner_id'))])
                if not supplise_id:
                    supplise_obj.create({'company_id_new':vals.get('contract_company1'),'partner_id':vals.get('partner_id')})
            return super(qdodoo_sms_create_contract, self).create(vals)

    @api.multi
    def write(self, vals):
        supplise_obj = self.env['supplise.ex']
        partner_id = vals.get('partner_id') if vals.get('partner_id') else self.partner_id.id
        contract_company1 = vals.get('contract_company1') if vals.get('contract_company1') else self.contract_company1.id
        if vals.get('partner_id') or vals.get('contract_company1'):
            if partner_id:
                supplise_ids = supplise_obj.search([('company_id_new','=',contract_company1),('partner_id','=',partner_id)])
                if not supplise_ids:
                    supplise_obj.create({'company_id_new':contract_company1,'partner_id':partner_id})
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

                message = '发个固定内容的短信'

                """
                message = content % (
                    partner_name, fields.Date.today(), vals.get('name', '') or self.name or u"XX合同",
                    vals.get('code', '') or self.code) or "**"
                """
                order_manager_id = vals.get('order_manager_id', False)
                if not order_manager_id:
                    raise except_orm(_(u'警告'), _(u'订单负责人为空'))
                user_id = user_obj.browse(order_manager_id)
                phone_number = '18863963084'

                #phone_number = user_id.phone or user_id.mobile or None

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
    """
    短信模板，嵌入系统配置中
    """
    _name = 'qdodoo.contract.order.sms.template'
    _inherit = 'res.config.settings'

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

class sendsms_before_oneday(models.Model):
    _name = 'sendsms.before.oneday'
    _description = '采购合同截止日期前前一天发送短信'

    def check_to_send(self, cr, uid):
        """
        根据采购->合同中设置的截止日期，在截止日期前一天发送短信
        该方法将由定时器调用
        """
        #短信模板
        sms_templat = u'（ERP人员）：这条信息来自于资源库，现有（供应商名称）于 （合同公司）下《合同》已到期。请关闭ERP系统中对应合作关系。如开通请按照《合同审批工作流》、《产品信息更改工作流》办理相关业务。'

        today = datetime.date.today()
        next_day = today+datetime.timedelta(days=1)

        #短信发送模块
        rs_send_obj = self.pool.get('rainsoft.sendsms')

        #遍历所有过期时间>=明天的记录，如果与今天仅差1天，则发短信
        analytic_obj = self.pool.get('account.analytic.account')
        analytic_ids = analytic_obj.search(cr, uid, [('date', '>=', next_day)])

        for analytic in analytic_obj.browse(cr, uid, analytic_ids):
            left_days = (datetime.datetime.strptime(analytic.date, '%Y-%m-%d').date() - today).days
            _logger.info('----->date:%s'%analytic.date)

            #过期时间与今天只晚一天的，发个短信
            if left_days == 1:
                order_manager_name = analytic.order_manager_id.name or 'No-Manager-Name'
                _logger.info(u'----->order_manager_name:{0:s}'.format(order_manager_name))
                phone_number = analytic.order_manager_id.partner_id.mobile or analytic.order_manager_id.partner_id.phone or None

                #供货方名称
                partner_name = analytic.partner_id.name or 'No-Partner-Name'

                #合同方公司
                company_name = analytic.company_id.name

                #合同名称
                contract_name = analytic.name

                sms_tosend = sms_templat.replace('ERP人员', order_manager_name, 1)\
                    .replace('供应商名称', partner_name, 1)\
                    .replace('合同公司', company_name, 1)\
                    .replace('《合同》', '《'+contract_name+'》', 1)

                _logger.info('----->phone:%s'%phone_number)
                _logger.info('----->sms:%s'%sms_tosend)

                if not phone_number == None:
                    res = rs_send_obj.send(cr, uid, phone_number, sms_tosend)
                    _logger.info(u'----->Send res:{0:s}'.format(res))
                else:
                    _logger.info(u'----->Phone{0:s}'.format(phone_number))

            else:
                _logger.info('----->Days:%s, more than 1day'%left_days)



