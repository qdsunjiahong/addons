# -*- coding: utf-8 -*-

from openerp import http, fields
from openerp import SUPERUSER_ID
from openerp.http import request
import logging

_logger = logging.getLogger(__name__)
import time
# url编码、http请求、json处理
import urllib, urllib2
import simplejson
import json
import random
import hashlib
import util
from urllib import urlencode
import os, sys
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["md5_crypt", "des_crypt"])


class qdoo_dd_work(http.Controller):
    @http.route(['/qdoo/dd/work'], type='http', auth="public", website=True)
    def get_didi(self, **post):
        """
        钉钉权限验证
        准备相关数据，输出页面调用钉钉客户端JSAPI来进行权限验证
        验证通过后
        """
        # 获取access_token
        corpid = 'dinge0b8fc92eb965404'
        corpsecret = 'MkKb_QDrtkwigaBar13AHo51xQLcJdnzLFiE_giow1kXeQUWLDH0K-1kC9gup7Zx'
        agentid = '10292872'
        url = 'https://oapi.dingtalk.com/gettoken?'
        args = {
            'corpid': corpid,
            'corpsecret': corpsecret
        }
        url += urlencode(args)
        response = urllib2.urlopen(url, timeout=60)
        result = json.loads(response.read())
        access_token = result.get('access_token')
        # 获取jsapi_ticket
        url_1 = 'https://oapi.dingtalk.com/get_jsapi_ticket?access_token=' + access_token + '&type=jsapi'
        response_1 = urllib2.urlopen(url_1, timeout=60)
        result_1 = json.loads(response_1.read())
        jsapi_ticket = result_1.get('ticket')
        # 生成一个随机字符串，不长于32位，主要保证签名不可预测
        nonceStr = ''
        chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        chars_length = len(chars) - 1
        for i in range(1, 16, 1):
            nonceStr += chars[random.randint(0, chars_length)]
        timeStamp = int(time.time())
        url = 'http://runbot.qdodoo.com/qdoo/dd/work'
        key_valu = {
            'noncestr': nonceStr,
            'timestamp': timeStamp,
            'jsapi_ticket': jsapi_ticket,
            'url': url,
        }
        _, prestr_new = util.params_filter(key_valu)
        key_valu['signature'] = hashlib.sha1(prestr_new).hexdigest()
        key_valu['corpId'] = corpid
        key_valu['agentId'] = agentid
        key_valu['access_token'] = access_token
        return request.website.render("qdodoo_dingtalk.didi2", key_valu)

    @http.route(['/qdoo/dd/work_details'], type='http', auth="public", website=True)
    def get_code(self, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        user_obj = pool.get('res.users')
        code = post.get('code')
        access_token = post.get('access_token')
        url = 'https://oapi.dingtalk.com/user/getuserinfo?access_token=%s&code=%s' % (access_token, code)
        response = urllib2.urlopen(url, timeout=60)
        # 获取钉钉用户信息
        result = json.loads(response.read())
        # {u'sys_level': 2, u'userid': u'65190347864', u'errcode': 0, u'is_sys': True, u'deviceId': u'00faaff1f6fea192d301ac83cfa550d3', u'errmsg': u'ok'}
        if result.get('userid'):
            userid = result.get('userid')
            user_id = user_obj.search(cr, SUPERUSER_ID, [('didi_id', '=', userid)])
            if user_id:
                # password=pwd_context.encrypt()
                url_red = 'http://runbot.qdodoo.com/web/works_details'
                login = user_obj.browse(cr, SUPERUSER_ID, user_id[0]).login
                passwd = user_obj.browse(cr, SUPERUSER_ID, user_id[0]).password
                info = "/login?db=%s&login=%s&key=%s&redirect=%s" % (request.session.db, login, passwd, url_red)
                return simplejson.dumps({'key': '1', 'info': info})
            else:
                return simplejson.dumps({'key': '2', 'info': u'系统中没有您的用户，请联系管理员增加！'})
        else:
            return simplejson.dumps({'key': '2', 'info': u'获取钉钉用户信息失败'})

    @http.route(['/web/works_details'], type='http', auth='public', website=True)
    def web_work_details(self, *kwargs):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        category_ids = pool.get('qdodoo.detail.category').search(cr, SUPERUSER_ID, [])
        category_ids2 = pool.get('qdodoo.detail.category').browse(cr, SUPERUSER_ID, category_ids)
        values = {}
        values['category_ids'] = category_ids2
        date_time = fields.Datetime.now()
        values['date_time'] = date_time
        return request.website.render("qdodoo_dingtalk.details_dd", values)

    @http.route(['/details_create'], type='http', auth='public', website=True)
    def details_create(self, **kwargs):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        category = kwargs.get('category')
        date_time = fields.datetime.now()
        text = kwargs.get('text')
        data = {
            'category_id': int(category),
            'c_date': date_time,
            'user_id': uid,
            'text': text
        }
        res=pool.get('qdodoo.work.details').create(cr, SUPERUSER_ID, data)
        return '1'

    @http.route(['/search/details'], type='http', auth='public', website=True)
    def search_detail(self, **kwargs):
        url = 'http://runbot.qdodoo.com/web?#page=0&limit=80&view_type=list&model=qdodoo.work.details&menu_id=556&action=732'
        ret = "<html><head><meta http-equiv='refresh' content='0;URL=%s'></head></html>" % url
        return ret
