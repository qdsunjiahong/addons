# -*- coding: utf-8 -*-
import werkzeug

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
import logging
from openerp.addons.website_sale.controllers.main import QueryURL, get_pricelist
_logger = logging.getLogger(__name__)
import time
#url编码、http请求、json处理
import urllib,urllib2
from lxml import etree
import json
import random
from datetime import datetime
import hashlib
from xml.etree.ElementTree import Element
import util
from urllib import urlencode
from werkzeug.utils import redirect
import os,sys
import requests.packages.urllib3.util.ssl_
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'

reload(sys)
sys.setdefaultencoding("utf-8")

class website_sale(http.Controller):
    def user_check(self):
        """
        该方法检查用户是否登陆，如未登陆，则向微信授权跳转
        """
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        config = pool.get('ir.config_parameter')
        if not request.session.has_key('user_id'):  #通过session信息判断是否登陆，修改为odoo登陆的session键
            wx_appid = config.get_param(cr, uid, 'wx_appid')  #微信服务号APPID
            wx_redirect = config.get_param(cr, uid, 'web.base.url') + '/wxsite/wxoauth'  #微信授权后的回调地址，不可包含GET参数
            wx_oauth_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid='+wx_appid+'&redirect_uri='+urllib.quote(wx_redirect, '')+'&response_type=code&scope=snsapi_userinfo&state=1#wechat_redirect'
            return redirect(wx_oauth_url)  #向微信授权跳转

    @http.route(['/wxsite/wxoauth'], type='http', auth="public", website=True, csrf=False)
    def wx_oauth(self, **post):
        """
        微信授权回调地址，用户同意授权后将带参(code）跳转入本地址
        根据code获取用户信息，用于比对该用户是否存在，不存在的则进行注册
        该授权正式实施前，开发者需要先到公众平台官网中的开发者中心页配置授权回调域名（如qdodoo.com）
        参考：http://mp.weixin.qq.com/wiki/4/9ac2e7b1f1d22e9e57260f6553822520.html
        """
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        wx_code = post['code']  #授权code，属于GET参数
        wx_state = post['state']  #跳转链接中的state参数，原样返回
        config = pool.get('ir.config_parameter')
        """
        根据code获取access token和openid
        """
        wx_appid = config.get_param(cr, uid, 'wx_appid')  #微信服务号APPID
        wx_appsecret = config.get_param(cr, uid, 'wx_appsecret')  #微信服务号APPSecret
        # wx_url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid='+wx_appid+'&secret='+wx_appsecret
        wx_url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid='+wx_appid+'&secret='+wx_appsecret+'&code='+wx_code+'&grant_type=authorization_code'
        response = urllib2.urlopen(wx_url)
        ret_json = response.read()
        ret_dict = json.loads(ret_json)  #解析json
        access_token = ret_dict['access_token']  #access_token
        wx_openid = ret_dict['openid']   #openid，微信用户唯一标识

        """
        在此处根据openid判断用户是否已存在数据库中
        """
        users_obj = pool.get('res.users')
        wx_user_exists = users_obj.search(cr, SUPERUSER_ID, [('login','=',wx_openid)])
        request.session['openid']=wx_openid

        """
        如果用户未加入数据库，则根据openid获取用户信息并注册用户
        """
        if not wx_user_exists:
            wx_url_info = 'https://api.weixin.qq.com/sns/userinfo?access_token='+access_token+'&openid='+wx_openid+'&lang=zh_CN'
            # wx_url_info = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token='+access_token+'&openid='+wx_openid+'&lang=zh_CN'
            response_info = urllib2.urlopen(wx_url_info)
            ret_json_info = response_info.read()
            ret_dict_info = json.loads(ret_json_info)  #解析json
            wx_nickname = ret_dict_info['nickname']  #微信用户昵称
            wx_country = ret_dict_info['country']  #微信用户所属国家，中国为CN
            wx_province = ret_dict_info['province']   #微信个人资料中所在省份，如：山东  该值可能为空
            wx_city = ret_dict_info['city']   #微信个人资料中所在城市，如：青岛  该值可能为空
            wx_sex = ret_dict_info['sex']   #性别  0：未知  1:男  2：女
            wx_headimgurl = ret_dict_info['headimgurl']   #微信用户头像地址。如: http://wx.qlogo.cn/mmopen/g3MonUZtNHkdmzicIlibx6iaFqAc56vxLSUfpb6n5WKSYVY0ChQKkiaJSgQ1dZuTOgvLLrhJbERQQ4eMsv84eavHiaiceqxibJxCfHe/46

            """
            以下可以是用户注册处理
            """
            users_obj.create(cr, SUPERUSER_ID, {'login':wx_openid,'name':wx_nickname,'password':'qdodoo'})
        return request.redirect("/login?db=%s&login=%s&key=%s&redirect=%s"%(request.session.db,wx_openid,'qdodoo','shop/wx/lunch'))

    @http.route(['/shop/wx/about'], type='http', auth="public", website=True, csrf=False)
    def get_about(self, **post):
        """
            进入支付页面，并传递数据
        """
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # 获取当前公司的名称（根据用户模型获取数据）
        users_obj = pool.get('res.users')
        company_obj = users_obj.browse(cr, SUPERUSER_ID, uid).company_id

        # 获取加入购物车的总金额
        all_car_num = 0
        car_obj = pool.get('qdodoo.wxsite.car')
        car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid)])
        for key_line in car_obj.browse(cr, SUPERUSER_ID, car_ids):
            all_car_num += key_line.number

        values={
            'company_obj':company_obj,
            'all_car_num': all_car_num,
        }

        return request.website.render("wxsite.about",values)

    @http.route(['/shop/wx/onchange'], type='http', auth="public", website=True, csrf=False)
    def get_onchange(self, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # 判断是如何修改数据
        # 删除数据
        try:
            # 获取操作的数据
            car_obj = pool.get('qdodoo.wxsite.car')
            car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid),('name','=',int(post.get('cartid')))])
            if car_ids:
                if post.get('action') == 'del':
                    car_obj.unlink(cr, SUPERUSER_ID, car_ids[0])
                if post.get('action') == 'update':
                    car_obj.write(cr, SUPERUSER_ID, car_ids[0], {'number':int(post.get('number'))})
            else:
                if post.get('action') == 'update':
                    car_obj.create(cr, SUPERUSER_ID, {'user_id':uid,'name':int(post.get('cartid')),'number':int(post.get('number'))})
            return '1'
        except ValueError, e:
            return '2'

    @http.route(['/shop/wx/car'], type='http', auth="public", website=True, csrf=False)
    def get_car(self, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # 获取当前公司的名称（根据用户模型获取数据）
        users_obj = pool.get('res.users')
        company_name = users_obj.browse(cr, SUPERUSER_ID, uid).company_id.name

        # 获取加入购物车的产品信息
        all_money = 0
        product_money = {} #小计
        product_num = {} #数量
        products = []
        car_obj = pool.get('qdodoo.wxsite.car')
        car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid),('number','>',0)])
        for key_line in car_obj.browse(cr, SUPERUSER_ID, car_ids):
            products.append(key_line.name)
            product_num[key_line.name] = key_line.number
            product_money[key_line.name] = key_line.number * key_line.name.lst_price
            all_money += key_line.number * key_line.name.lst_price #获取总金额

        values={
            'company_name':company_name,
            'product_money': product_money,
            'products':products,
            'all_money':all_money,
            'product_num':product_num,
        }
        return request.website.render("wxsite.car",values)

    # 产品加入购物车
    @http.route(['/ajax/addtocart'], type='http', auth="public", website=True, csrf=False)
    def get_addtocart(self, **post):
        try:
            cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
            car_obj = pool.get('qdodoo.wxsite.car')
            car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid),('name','=',int(post.get('pid')))])
            if car_ids:
                for car_id in car_obj.browse(cr, SUPERUSER_ID, car_ids):
                    car_obj.write(cr, SUPERUSER_ID, car_id.id, {'number':car_id.number + int(post.get('num'))})
            else:
                car_obj.create(cr, SUPERUSER_ID, {'name':int(post.get('pid')),'number':int(post.get('num')), 'user_id':uid})
            return '1'
        except ValueError, e:
            return '2'

    @http.route(['/shop/wx/order'], type='http', auth="public", website=True, csrf=False)
    def get_order(self, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # 获取当前登录人的客户
        users_obj = pool.get('res.users')
        partner_obj = users_obj.browse(cr, SUPERUSER_ID, uid).partner_id
        # 获取订单信息
        order_obj = pool.get('pos.order')
        order_ids = order_obj.search(cr, SUPERUSER_ID, [('partner_id','=',partner_obj.id),('state','!=','cancel')])
        orders = order_obj.browse(cr, SUPERUSER_ID, order_ids)

        # 获取加入购物车的总数量
        all_car_num = 0

        car_obj = pool.get('qdodoo.wxsite.car')
        car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid)])
        for key_line in car_obj.browse(cr, SUPERUSER_ID, car_ids):
            all_car_num += key_line.number

        values={
            'all_car_num': all_car_num,
            'orders':orders,
        }

        return request.website.render("wxsite.order",values)

    @http.route(['/shop/wx/user'], type='http', auth="public", website=True, csrf=False)
    def get_user(self, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        user_obj = pool.get('res.users')
        user_name = user_obj.browse(cr, SUPERUSER_ID, uid).name

        # 获取加入购物车的总数量
        all_car_num = 0
        car_obj = pool.get('qdodoo.wxsite.car')
        car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid)])
        for key_line in car_obj.browse(cr, SUPERUSER_ID, car_ids):
            all_car_num += key_line.number

        values={
            'user_name':user_name,
            'all_car_num': all_car_num,
        }

        return request.website.render("wxsite.user",values)

    @http.route(['/shop/wx/lunch',
                 '/shop/wx/lunch/<model("product.public.category"):category>',], type='http', auth="public", website=True, csrf=False)
    def tracking_cart(self, category=None , **post):
        """
        站点首页
        """
        # 先校验是否登录
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # 3代表公开用户，也就是未登录状态
        if uid == 3:
            return self.user_check()
        else:
            category_obj = pool.get('pos.category')
            # 组织数据查询时的条件
            domain = [("sale_ok", "=", True),("available_in_pos","=",True)]
            if category:
                domain += [('pos_categ_id', 'child_of', int(category))]
                category = category_obj.browse(cr, SUPERUSER_ID, int(category), context=context)

            # 获取当前公司的名称（根据用户模型获取数据）
            users_obj = pool.get('res.users')
            company_name = users_obj.browse(cr, SUPERUSER_ID, uid).company_id.name

            # 获取所有的产品模板数据
            template_obj = pool.get('product.template')
            product_ids = template_obj.search(cr, SUPERUSER_ID, domain)
            products = template_obj.browse(cr, SUPERUSER_ID, product_ids, context=context)

            # 获取该产品是否已加入到了购物车
            key_name = {}
            all_car_num = 0
            all_money = 0
            car_obj = pool.get('qdodoo.wxsite.car')
            car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid),('name','in',product_ids)])
            for key_line in car_obj.browse(cr, SUPERUSER_ID, car_ids):
                key_name[key_line.name.id] = key_line.number
                all_car_num += key_line.number
                all_money += key_line.number * key_line.name.lst_price #获取总金额

            category_ids = category_obj.search(cr, SUPERUSER_ID, [('parent_id', '=', False)], context=context)
            categs = category_obj.browse(cr, SUPERUSER_ID, category_ids, context=context)

            keep = QueryURL('/shop/wx/lunch', category=category and int(category))

            if not context.get('pricelist'):
                pricelist = get_pricelist()
                context['pricelist'] = int(pricelist)
            else:
                pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)

            from_currency = pool['res.users'].browse(cr, uid, uid, context=context).company_id.currency_id
            to_currency = pricelist.currency_id
            compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
            values={
                'company_name':company_name,
                'products': products,
                'category': category,
                'categories': categs,
                'keep': keep,
                'compute_currency':compute_currency,
                'pricelist': pricelist,
                'key_name':key_name,
                'all_car_num':all_car_num,
                'all_money':all_money,
            }
            return request.website.render("wxsite.products",values)

    @http.route(['/shop/wx/product/<model("product.template"):product>'], type='http', auth="public", website=True, csrf=False)
    def product(self, product, category='', **kwargs):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        category_obj = pool['product.public.category']
        template_obj = pool['product.template']

        context.update(active_id=product.id)

        if category:
            category = category_obj.browse(cr, uid, int(category), context=context)

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int,v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        keep = QueryURL('/shop/wx/lunch', category=category and category.id, attrib=attrib_list)

        category_ids = category_obj.search(cr, uid, [], context=context)
        category_list = category_obj.name_get(cr, uid, category_ids, context=context)
        category_list = sorted(category_list, key=lambda category: category[1])

        pricelist = get_pricelist()

        from_currency = pool['res.users'].browse(cr, uid, uid, context=context).company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)

        if not context.get('pricelist'):
            context['pricelist'] = int(get_pricelist())
            product = template_obj.browse(cr, 1, int(product), context=context)

        # 获取该产品是否已加入到了购物车
        key_name = {}
        all_car_num = 0
        car_obj = pool.get('qdodoo.wxsite.car')
        car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid)])
        for key_line in car_obj.browse(cr, SUPERUSER_ID, car_ids):
            key_name[key_line.name.id] = u'已添加'
            all_car_num += key_line.number

        # 获取当前公司的名称（根据用户模型获取数据）
        users_obj = pool.get('res.users')
        company_name = users_obj.browse(cr, SUPERUSER_ID, uid).company_id.name

        values = {
            'category': category,
            'pricelist': pricelist,
            'attrib_values': attrib_values,
            'compute_currency': compute_currency,
            'attrib_set': attrib_set,
            'keep': keep,
            'category_list': category_list,
            'main_object': product,
            'product': product,
            'company_name':company_name,
            'all_car_num':all_car_num,
            'key_name':key_name,
        }
        return request.website.render("wxsite.product", values)

    def json2xml(self, json):
        string = ""
        for k, v in json.items():
            string = string + "<%s>" % (k) + str(v) + "</%s>" % (k)

        return string

    @http.route(['/shop/wx/wxpay'], type='http', auth="public", website=True, csrf=False)
    def wx_pay(self, **post):
        """
        微信JSAPI支付，调用链接如：http://www.qdodoo.com/wxsite/wxpay/20160107125945356，其中20160107125945356是订单号
        需先到微信公众号平台配置支付授权目录（如：http://www.qdodoo.com/wxsite/wxpay/）——也可以配置测试目录，但测试有一定限制，因此可以直接在正式环境中使用1分钱订单测试
        还需到微信商户平台（pay.weixin.qq.com）-->账户设置-->API安全-->密钥设置中设置密钥，对应本函数中的wx_key
        参考：https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=7_1
        """
        cr, uid, context, pool = request.cr,request.uid, request.context, request.registry
        # 获取当前公司的名称（根据用户模型获取数据）
        users_obj = pool.get('res.users')
        users = users_obj.browse(cr, SUPERUSER_ID, uid)
        company_name = users.company_id.name
        partner_id = users.partner_id.id
        order_obj = pool.get('pos.order')
        if post.get('oid'):
            res_order_id = int(post.get('oid'))
            all_money = float(post.get('money'))
            all_car_num = 0
            for order in order_obj.browse(cr, SUPERUSER_ID, res_order_id).lines:
                all_car_num += order.qty
        else:
            car_obj = pool.get('qdodoo.wxsite.car')
            car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid)])
            # 生成销售订单（POS）
            order_line_obj = pool.get('pos.order.line')
            res_order_id = order_obj.create(cr, SUPERUSER_ID, {'partner_id':partner_id,'pricelist_id':1})

            # 获取加入购物车的总金额
            all_money = 0
            all_car_num = 0
            for key_line in car_obj.browse(cr, SUPERUSER_ID, car_ids):
                all_money += key_line.number * key_line.name.lst_price #获取总金额
                all_car_num += key_line.number
                # 生成销售单明细
                order_line_obj.create(cr, SUPERUSER_ID, {'order_id':res_order_id,'product_id':key_line.name.id,
                                                         'qty':key_line.number,'price_unit':key_line.name.lst_price})
            car_obj.unlink(cr, SUPERUSER_ID, car_ids)


        wx_openid = request.session['openid']    #微信用户openid
        config = pool.get('ir.config_parameter')
        #下面几个变量是微信支付相关配置
        wx_appid = config.get_param(cr, uid, 'wx_appid')    #公众号号APPID，通常是微信签约时的服务号APPID
        wx_mchid = config.get_param(cr, uid, 'wx_mchid')  #商户号，签约微信支付后分配的商户号
        wx_key = config.get_param(cr, uid, 'wx_key')  #微信支付密钥，到微信商户平台设置并填写此处
        wx_pay_backnotify = config.get_param(cr, uid, 'web.base.url') + '/shop/wx/backnotify'  #接收微信支付异步通知地址，不可携带参数

        #生成一个随机字符串，不长于32位，主要保证签名不可预测
        nonce_str = ''
        chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        chars_length = len(chars) - 1
        for i in range(1, 32, 1):
            nonce_str += chars[random.randint(0, chars_length)]
        spbill_create_ip = config.get_param(cr, uid, 'spbill_create_ip')
        if res_order_id < 10:
            res_order_id = '0' + str(res_order_id)
        #微信统一下单接口所需参数
        wx_oparam = {
            'appid': wx_appid,   #公众号号APPID
            'mch_id': wx_mchid,  #商户号
            'nonce_str': nonce_str,
            'body': u'点餐订单',  #支付单简要描述
            'out_trade_no': res_order_id,  #商户订单号
            'total_fee': int(all_money * 100),  #支付金额，单位为“分”，所以要x100
            'spbill_create_ip': spbill_create_ip,  #用户端IP地址，此处我不知道怎么获取
            'notify_url': wx_pay_backnotify,  #异步通知地址
            'trade_type': 'JSAPI',  #交易类型
            'openid': wx_openid,  #微信用户openid，交易类型为jsapi时，此参数必传
            'attach': 'wxsite',  #附加数据，用于商户携带自定义数据，在查询API和支付通知中原样返回，可选填，但不要留空
        }

        """
        参数签名，将非空字典键值按ASCII码升序排列，然后按url键值对拼接，最后拼接上微信支付密钥key
        将所拼接的字符串进行MD5运算，再将得到的字符串中所有字母转换为大写。即是签名
        """

        _, prestr = util.params_filter(wx_oparam)
        wx_oparam['sign'] = hashlib.md5(prestr + '&key=' +wx_key).hexdigest().upper()
        data_xml = "<xml>" + self.json2xml(wx_oparam) + "</xml>"
        url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'  #接口地址
        request_new = urllib2.Request(url, data_xml)
        res = urllib2.urlopen(request_new)
        return_xml = etree.fromstring(res.read())
        error_text = ''
        _logger.info('111111111:%s'%data_xml)
        if return_xml.find('return_code').text == 'SUCCESS':
            if return_xml.find('result_code').text == 'SUCCESS':
                prepay_id = return_xml.find('prepay_id').text  #预下单编号

                #再生成一个随机字符串，不长于32位，仍然是保证接下来签名不可预测
                nonce_str = ''
                for i in range(1, 32, 1):
                    nonce_str += chars[random.randint(0, chars_length)]

                #JSAPI支付所需数据
                wx_pay_dict = {
                    'appId': wx_appid,  #微信公众号APPID
                    'timeStamp': str(time.time()),  #当前Unix时间戳
                    'nonceStr': nonce_str,  #随机字符串
                    'package': 'prepay_id='+prepay_id,  #订单详情扩展，主要填写统一下单接口返回的预下单编号
                    'signType': 'MD5',  #签名算法，目前仅支持MD5
                }
                _, prestr_new = util.params_filter(wx_pay_dict)
                wx_pay_dict['paySign'] = hashlib.md5(prestr_new + '&key=' +wx_key).hexdigest().upper()

                #转换成json格式，将在页面js脚本中使用该数据
                wx_pay_json = json.dumps(wx_pay_dict)

                #显示微信支付页面
                values = {
                    'pay_json': wx_pay_json,
                    'company_name':company_name,
                    'all_car_num': all_car_num,
                    'all_money':all_money,
                }
                return request.website.render("wxsite.wxpay", values)
            else:
                if return_xml.find('err_code').text:
                    error_text = error_text + u'错误代码为：' + return_xml.find('err_code').text
                elif return_xml.find('err_code_des').text:
                    error_text = error_text + '\n' + return_xml.find('err_code_des').text
                else:
                    error_text = u'交易发起失败，请稍后重试！'
        else:
            if return_xml.find('return_msg').text:
                error_text = return_xml.find('return_msg').text
            else:
                error_text = u'交易发起失败，请稍后重试！'
        values = {
            'company_name':company_name,
            'error_text':error_text,
            'all_car_num':all_car_num,
        }
        return request.website.render("wxsite.error", values)

    def pos_id(self):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        printer_obj = pool.get('restaurant.printer')
        printer_ids = printer_obj.search(cr, SUPERUSER_ID, [])
        dict_ip = {}
        for printer_ids in printer_obj.browse(cr, SUPERUSER_ID, printer_ids):
            for line in printer_ids.product_categories_ids:
                dict_ip[line.id] = printer_ids.proxy_ip
        return dict_ip

    @http.route('/shop/wx/backnotify', type='http', auth='none', methods=['POST'], csrf=False)
    def wxpay_backnotify(self, **post):
        """
        微信支付异步通知地址
        当用户成功支付后，微信服务器会POST一份xml格式的支付信息到该地址，通过商户订单号和支付状态进行处理
        处理后需返回一个xml信息，格式示例：
        <xml>
            <return_code><![CDATA[success]]></return_code>
            <return_msg><![CDATA[OK]]></return_msg>
        </xml>
        参考：https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=9_7
        """
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        config = pool.get('ir.config_parameter')
        #下面几个变量是微信支付相关配置
        wx_key = config.get_param(cr, uid, 'wx_key')  #微信支付密钥，到微信商户平台设置并填写此处
        order_obj = pool.get('pos.order')
        payment_obj = pool.get('pos.make.payment')
        config_obj = pool.get('pos.config')
        print_list_obj = pool.get('qdodoo.print.list')
        dict_post_ip = self.pos_id()
        config_id = config_obj.search(cr, SUPERUSER_ID, [('iface_print_via_proxy','=',True)])
        if config_id:
            proxy_ip = config_obj.browse(cr, SUPERUSER_ID, config_id[0]).proxy_ip
        # 有返回结果
        if post:
            #解析post过来的xml数据，获取必要的信息
            post_dict = json.loads(post)  #解析json为dict

            #需返回给微信的参数，默认处理成功
            ret_dict = {
                'return_code': 'SUCCESS',
                'return_msg': 'OK',
            }

            #如果支付成功，则进行处理
            if post_dict['return_code'] == 'SUCCESS':
                #对post过来的数据进行签名，与post参数中的签名sign进行对比
                post_sign_dict = {}  #捡取非空参数，不包含签名sign
                for key, val in post_dict.items():
                    if not val == '' and not key == 'sign':
                        post_sign_dict[key] = val

                post_sign_dict = sorted(post_sign_dict.iteritems(), key=lambda d:d[0])
                post_sign_keyval = ''
                for key, val in post_sign_dict.items():
                    post_sign_keyval += key+'='+val+'&'
                post_sign_keyval += 'key='+wx_key
                post_sign = hashlib.new("md5", post_sign_keyval).hexdigest().upper()  #根据微信post来的参数计算出的签名

                if post_sign == post_dict['sign']:  #自己计算出来的签名与微信post过来的sign签名一致，则验签通过
                    oid = post_dict['out_trade_no']  #商户订单号，与发起微信支付时填写的out_trade_no一致，可据此处理对应订单
                    if oid[0] == '0':
                        oid = oid[1:]
                    wxpay_qid = post_dict['transaction_id']  #微信支付交易流水号，可据此对账
                    wxpay_sum = int(post_dict['total_fee'])/100  #实际支付金额，单位：分，除以100转换成元

                    #基本以上参数足够处理订单，以下也是post中必含的参数，可酌情使用
                    wxpay_openid = post_dict['openid']  #支付的微信用户openid，原则上与发起支付的openid一致
                    wxpay_tradetype = post_dict['trade_type']  #支付方式，原则上与发起支付的方式一致，如JSAPI
                    wxpay_appid = post_dict['appid']  #公众号APPID
                    wxpay_mch_id = post_dict['mch_id']  #商户号
                    wxpay_banktype = post_dict['bank_type']  #银行类型，标识所代表的银行可参考官方说明
                    wxpay_endtime = post_dict['time_end']  #支付完成时间，格式：yyyyMMddHHmmss，如：20160108124035

                    """
                    下面可以根据以上获取的参数对订单进行处理
                    小提示：微信可能多次发送同一笔支付通知，因此需先检验该订单支付是否已经处理过，未处理过的才进行处理
                    比如更改订单状态、财务出入帐等
                    """
                    order_obj.signal_workflow(cr, SUPERUSER_ID, [int(oid)], 'paid')

                else:  #验签失败
                    ret_dict['code'] = 'fail'
                    ret_dict['desc'] = 'sign valid fail'

            #最终，要返回处理结果的xml格式数据
            wxpay_ret_xml = Element('xml')
            for key, val in ret_dict.items():
                xml_child = Element(key)
                xml_child.text = str(val)
                wxpay_ret_xml.append(xml_child)
            return wxpay_ret_xml
        else:
            # 没有返回结果，执行查询方法
            wx_add = 'https://api.mch.weixin.qq.com/pay/orderquery'
            wx_appid = config.get_param(cr, uid, 'wx_appid')    #公众号号APPID，通常是微信签约时的服务号APPID
            wx_mchid = config.get_param(cr, uid, 'wx_mchid')  #商户号，签约微信支付后分配的商户号
            # 查询所有未完成的订单
            order_ids = order_obj.search(cr, SUPERUSER_ID, [('state','=','draft')])
            for order_ids in order_ids:
                #生成一个随机字符串，不长于32位，主要保证签名不可预测
                nonce_str = ''
                chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
                chars_length = len(chars) - 1
                for i in range(1, 32, 1):
                    nonce_str += chars[random.randint(0, chars_length)]
                #微信查询接口所需参数
                wx_search = {
                    'appid': wx_appid,   #公众号号APPID
                    'mch_id': wx_mchid,  #商户号
                    'nonce_str': nonce_str,
                    'out_trade_no': order_ids,  #商户订单号
                }

                """
                参数签名，将非空字典键值按ASCII码升序排列，然后按url键值对拼接，最后拼接上微信支付密钥key
                将所拼接的字符串进行MD5运算，再将得到的字符串中所有字母转换为大写。即是签名
                """

                _, prestr_select = util.params_filter(wx_search)
                wx_search['sign'] = hashlib.md5(prestr_select + '&key=' +wx_key).hexdigest().upper()
                data_xml = "<xml>" + self.json2xml(wx_search) + "</xml>"
                request_new = urllib2.Request(wx_add, data_xml)
                res = urllib2.urlopen(request_new)
                return_xml = etree.fromstring(res.read())
                if return_xml.find('return_code').text == "SUCCESS" and return_xml.find('result_code').text != 'FAIL':
                    pay_state = return_xml.find('trade_state').text #交易状态
                    pos_id = return_xml.find('out_trade_no').text #订单号
                    pos_obj = order_obj.browse(cr, SUPERUSER_ID, int(pos_id))
                    if pay_state == 'SUCCESS':
                        res_id = payment_obj.create(cr, SUPERUSER_ID, {'journal_id':pos_obj.session_id.config_id.journal_ids[0].id,
                                                              'amount':pos_obj.amount_total,'payment_name':u'微信支付',
                                                              'payment_date':datetime.now().date()})
                        payment_obj.check(cr, SUPERUSER_ID, [res_id], context={'active_id':pos_obj.id})
                        infomation = """<receipt align="center" value-thousands-separator="" width="40">
                            <div font="b">
                                    <div>%s</div>
                                    <div>电话：%s</div>
                                    <div>%s</div>
                                    <div>%s</div>
                                    <div>--------------------------------</div>
                                    <div>被服务于 %s</div>
                            </div>
                            <br/><br/>
                            <div line-ratio="0.6">"""%(pos_obj.company_id.name,pos_obj.company_id.phone,pos_obj.company_id.email,
                                                       pos_obj.company_id.website,pos_obj.user_id.name)
                        # 循环订单明细
                        for line in pos_obj.lines:
                            infomation += """++++++<line><left>%s</left></line>
                            <line indent="1">
                                <left>
                                    <value value-autoint="on" value-decimals="3">
                                        %s
                                    </value>
                                        %s

                                    x

                                    <value value-decimals="2">

                                        %s

                                    </value>
                                    ===%s===
                                </left>
                                <right>
                                    <value>%s</value>
                                </right>
                            </line>++++++"""%(line.product_id.name,line.qty,line.product_id.uom_id.name,line.product_id.list_price,
                           dict_post_ip.get(line.product_id.pos_categ_id.id), line.product_id.list_price)

                        infomation += """</div>
                            <line><right>--------</right></line>
                            <line size="double-height">
                                <left><pre>        合计</pre></left>
                                <right><value>%s</value></right>
                            </line>
                            <br/><br/>
                                <line>
                                    <left>现金 (CNY)</left>
                                    <right><value>%s</value></right>
                                </line>
                            <br/>
                            <line size="double-height">
                                <left><pre>        CHANGE</pre></left>
                                <right><value>0</value></right>
                            </line>
                            <br/>
                            <br/>
                            <div font="b">
                                <div>Order %s</div>
                                <div>%s</div>
                            </div>
                        </receipt>"""%(pos_obj.amount_total,pos_obj.amount_total,pos_obj.name,datetime.now())
                        print_list_obj.create(cr, SUPERUSER_ID, {'name':infomation,'is_print':False})
                    elif pay_state == 'USERPAYING':
                        pass
                    else:
                        order_obj.signal_workflow(cr, SUPERUSER_ID, [int(pos_id)], 'cancel')
                else:
                    pass
            return 'SUCCESS'