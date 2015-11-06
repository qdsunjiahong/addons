# -*- encoding:utf-8 -*-

from openerp.osv import osv, fields
from xml.etree import ElementTree
import httplib, urllib
from datetime import datetime, timedelta
import re
import time


class rainsoft_sms_config(osv.osv):
    _name = 'rainsoft.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'user_id': fields.char(u'用户ID', Help='user id that service provider gives to you'),
        'send_address': fields.char(u'接口', Help='The address that your sms send to'),
        'user_name': fields.char(u'账号', Help='The username that can pass interface'),
        'pass_word': fields.char(u'密码', password=True),
        'appendix': fields.char(u'结尾', Help="The text that append to every message's end"),
        # 'model_price': fields.boolean("Allow Import Price From Excel File"),
        # 'sheet_name': fields.text('Sheet Names'),
    }

    def get_default_val(self, cr, uid, fields, context=None):
        user_id = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.userid", context=context),
        send_address = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.address", context=context)
        username = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.username", context=context)
        password = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.password", context=context)
        appendix = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.appendix", context=context)
        # model_price = self.pool.get('ir.config_parameter').get_param(cr, uid, "rainsoft.sms.model_price",
        # context=context)
        # sheet_names = self.pool.get('ir.config_parameter').get_param(cr, uid, "rainsoft.sms.sheet_name",
        # context=context)
        res = {"user_id": user_id, "send_address": send_address, "user_name": username, "pass_word": password,
               "appendix": appendix}
        return res

    def set_default_val(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get('ir.config_parameter')
        for record in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, 'rainsoft.sms.userid', record.user_id),
            config_parameters.set_param(cr, uid, 'rainsoft.sms.address', record.send_address, context=context)
            config_parameters.set_param(cr, uid, 'rainsoft.sms.username', record.user_name, context=context)
            config_parameters.set_param(cr, uid, 'rainsoft.sms.password', record.pass_word, context=context)
            config_parameters.set_param(cr, uid, 'rainsoft.sms.appendix', record.appendix, context=context)
            # config_parameters.set_param(cr, uid, 'rainsoft.sms.model_price', record.model_price, context=context)
            # config_parameters.set_param(cr, uid, 'rainsoft.sms.sheet_name', record.sheet_name, context=context)

    def default_get(self, cr, uid, fields, context=None):
        res = super(rainsoft_sms_config, self).default_get(cr, uid, fields, context)
        return res


class rainsoft_send_sms(osv.osv):
    _name = 'rainsoft.sendsms'
    _description = 'Text Message Interface'

    def send(self, cr, uid, mobile, content, context=None):
        user_id = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.userid", context=context),
        send_address = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.address", context=context)
        username = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.username", context=context)
        password = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.password", context=context)
        appendix = self.pool.get("ir.config_parameter").get_param(cr, uid, "rainsoft.sms.appendix", context=context)

        httpclient = None
        res = {}
        try:
            params = urllib.urlencode({
                "action": "send",
                "userid": int(user_id[0]),
                "account": username,
                "password": password,
                "mobile": mobile,
                "content": content + appendix,
                "sendTime": '',
                "extno": '',
            })

            address = send_address.split(':')
            port = len(address) > 1 and address[1] or 80

            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            httpclient = httplib.HTTPConnection(address[0], int(port), timeout=30)
            httpclient.request("POST", "/sms.aspx", params, headers)

            response = httpclient.getresponse()
            result = response.read()

            # handle the xml result.
            root = ElementTree.fromstring(result)
            lst_node = root.getiterator("returnstatus")
            for node in lst_node:
                res['status'] = node.text
            mes_node = root.getiterator("message")
            res['message'] = mes_node[0].text
        except Exception, e:
            print e
        finally:
            if httpclient:
                httpclient.close()
            return res


class auto_email_template_data(osv.osv):
    _name = 'auto.mail.template.data'
    _columns = {
        'title': fields.char(u'标题'),
        'body_html': fields.html(u'内容'),
    }


class auto_sms_template_data(osv.osv):
    _name = 'auto.sms.template.data'
    _columns = {
        'title': fields.char(u'标题'),
        'body': fields.html(u'内容')
    }


class qdodoo_account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'

    def send_sms(self, cr, uid, context=None):
        if context == None:
            context = {}
        content = self.pool.get('auto.mail.template.data').browse(cr, uid, 1, context=context).body_html
        date_now = datetime.now()
        time_now = datetime.strptime(str(date_now + timedelta(days=0))[:10], '%Y-%m-%d')
        date1 = datetime.strptime(str(date_now + timedelta(days=45))[:10], '%Y-%m-%d')
        date2 = datetime.strptime(str(date_now + timedelta(days=15))[:10], '%Y-%m-%d')
        message_list1 = self.pool.get('account.analytic.account').search(cr, uid,
                                                                         [('date', '>', date2), ('date', '<=', date1),
                                                                          ('sms_one_ok', '=', False),
                                                                          ('state', 'not in', ('close', 'cancelled'))
                                                                          ], context=context)
        rs_send_service = self.pool.get('rainsoft.sendsms')
        if len(message_list1):
            for line in self.pool.get('account.analytic.account').browse(cr, uid, message_list1, context=context):
                phone_number = line.manager_id.mobile or line.manager_id.phone
                type_contact = line.contract_type1.name
                mm = content % (line.partner_id.name, line.name, line.days)
                message = (re.sub('<[^>]+>', '', mm))
                if phone_number and type_contact != u'采购批次合同':
                    res = rs_send_service.send(cr, uid, phone_number, message, context=context)
                    if res['message'] == 'ok':
                        line.write({'sms_one_ok': True, 'contract_state': u'即将到期'})
                    else:
                        pass
                else:
                    pass

        message_list2 = self.pool.get('account.analytic.account').search(cr, uid,
                                                                         [('date', '<=', date2),
                                                                          ('date', '>', time_now),
                                                                          ('sms_two_ok', '=', False),
                                                                          ('state', 'not in', ('close', 'cancelled'))],
                                                                         context=context)
        if len(message_list2):
            for line in self.pool.get('account.analytic.account').browse(cr, uid, message_list2, context=context):
                phone_number = line.manager_id.mobile or line.manager_id.phone
                type_contact = line.contract_type1.name
                mm = content % (line.partner_id.name, line.name, line.days)
                message = (re.sub('<[^>]+>', '', mm))
                if phone_number and type_contact != u'采购批次合同':
                    res = rs_send_service.send(cr, uid, phone_number, message, context=context)
                    if res['message'] == 'ok':
                        line.write({'sms_two_ok': True, 'contract_state': u'即将到期'})
                    else:
                        pass
                else:
                    pass
    def send_sms2(self, cr, uid, context=None):
        if context == None:
            context = {}
        content = self.pool.get('auto.sms.template.data').browse(cr, uid, 1, context=context).body
        date_now = datetime.now()
        rs_send_service = self.pool.get('rainsoft.sendsms')
        time_now = datetime.strptime(str(date_now + timedelta(days=0))[:10], '%Y-%m-%d')
        date1 = datetime.strptime(str(date_now + timedelta(days=45))[:10], '%Y-%m-%d')
        date2 = datetime.strptime(str(date_now + timedelta(days=15))[:10], '%Y-%m-%d')
        message_list = self.pool.get('account.analytic.account').search(cr, uid,
                                                                        [('date', '<=', date2),
                                                                         ('date', '>', time_now),
                                                                         ('erp_ok', '=', False),
                                                                         ('state', 'not in', ('close', 'cancelled'))],
                                                                        context=context)
        if message_list:
            for line in self.pool.get('account.analytic.account').browse(cr, uid, message_list, context=context):
                for i in line.erp_manager_ids:
                    phone_number = i.mobile or i.phone
                    mm = content % (i.name, line.partner_id.name, line.name)
                    message = (re.sub('<[^>]+>', '', mm))
                    if phone_number:
                        res2 = rs_send_service.send(cr, uid, phone_number, message, context=context)
                        if res2['message'] == 'ok':
                            line.write({'erp_ok': True})
