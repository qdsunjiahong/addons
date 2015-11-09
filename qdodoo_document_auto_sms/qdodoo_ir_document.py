# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from datetime import datetime, timedelta
import re


class ir_document(models.Model):
    _inherit = 'ir.attachment'

    once_ok = fields.Boolean(string=u'第一次提醒')
    twice_ok = fields.Boolean(string=u'第二次提醒')

    @api.model
    def send_sms(self):
        content = self.env["ir.config_parameter"].get_param("document.sms.body")
        rs_send_service = self.env['rainsoft.sendsms']
        # date_now = fields.Date.today()
        date_now = datetime.now()
        date_n = fields.date.today()
        date_15_e = date_now + timedelta(days=15)
        date_45_e = date_now + timedelta(days=45)
        date_15 = str(date_15_e)[:10]
        date_45 = str(date_45_e)[:10]
        result_15_list = []
        result_45_list = []
        ir_attachment_45 = self.search(
            [('attachment_endtime', '<=', date_45), ('attachment_endtime', '>', date_15), ('once_ok', '=', False)])
        ir_attachment_15 = self.search(
            [('attachment_endtime', '<=', date_15), ('attachment_endtime', '>=', date_n), ('twice_ok', '=', False)])
        if ir_attachment_45:
            for ir_45 in ir_attachment_45:
                if not ir_45.user_id.phone and not ir_45.user_id.mobile:
                    continue
                elif ir_45.user_id.phone or ir_45.user_id.mobile:
                    phone_number = ir_45.user_id.mobile or ir_45.user_id.phone
                    result_45_list.append((ir_45.user_id.name, phone_number, ir_45.name, ir_45))
        if ir_attachment_15:
            for ir_15 in ir_attachment_15:
                if not ir_15.user_id.phone and not ir_15.user_id.mobile:
                    continue
                elif ir_15.user_id.phone or ir_15.user_id.mobile:
                    phone_number = ir_15.user_id.mobile or ir_15.user_id.phone
                    result_15_list.append((ir_15.user_id.name, phone_number, ir_15.name, ir_15))
        if result_45_list:
            for i in result_45_list:
                end_datetime = i[-1].attachment_endtime
                period = datetime.strptime(end_datetime, '%Y-%m-%d') - datetime.now()
                days = period.days
                message_s = content % (i[-1].partner_id.name, i[-1].name, days)
                res = rs_send_service.send(i[1], message_s)
                if res['message'] == "ok":
                    i[-1].write({'once_ok': True})
        if result_15_list:
            for k in result_15_list:
                end_datetime = k[-1].attachment_endtime
                period = datetime.strptime(end_datetime, '%Y-%m-%d') - datetime.now()
                days = period.days
                message_s = content % (k[-1].partner_id.name, k[-1].name, days)
                res = rs_send_service.send(k[1], message_s)
                if res['message'] == "ok":
                    k[-1].write({'twice_ok': True})


class qdodoo_sms_document_data(models.Model):
    _name = 'qdodoo.sms.document.data'
    _inherit = 'res.config.settings'
    _description = 'qdodoo.sms.document.data'

    body = fields.Text(string=u'模板内容', required=True)

    @api.multi
    def get_default_val(self):
        body = self.env['ir.config_parameter'].get_param('document.sms.body')

        res = {"body": body}
        return res

    @api.multi
    def set_default_val(self):
        config_parameters = self.env['ir.config_parameter']
        for record in self.browse(self.ids):
            config_parameters.set_param('document.sms.body', record.body)

    @api.model
    def default_get(self, fields):
        res = super(qdodoo_sms_document_data, self).default_get(fields)
        return res
