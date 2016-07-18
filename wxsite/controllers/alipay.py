#  -*- coding: utf-8 -*-
import main
from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)

# url编码、http请求、json处理
import urllib,urllib2
import json
import util
import datetime
from werkzeug.utils import redirect
import os,sys
from lxml import etree

# RSA加解密
from Crypto.PublicKey import RSA
from OpenSSL.crypto import load_privatekey, FILETYPE_PEM, sign
import base64
import httplib

# MD5加密
import hashlib


class alipay_fuwu(main.website_sale):


    @http.route(['/alipay/fuwu/rec'], type='http', auth="public", website=True, csrf=False)
    def alipay_fuwu(self, **post):
        """
        支付宝服务窗开发者模式验证和消息接受地址
        """

        # 将post来的参数排除掉sign后作为待签名参数
        sign_params_dic = {}
        for post_key, post_val in post.items():
            if not post_key=='sign':
                sign_params_dic[post_key] = post_val.decode('utf8')

        # 待签名参数按key值排序，组合成query字符串
        _, sign_query_str = util.params_filter(sign_params_dic)

        # 使用支付宝公钥签名验签
        sign_verify = RSA.load_pub_key('addons-extra/wxsite/static/alipay_rsa_public_key.pem').verify(sign_query_str, post['sign'])
        # sign_by_ali_pub64 = sign_by_ali_pub.encode('base64')

        if sign_verify:
            # 待签名字符串：公钥+success
            str_to_sign_by_private = '<biz_content>MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC9vK4cSuzfGJKMJ/XQ82SMxRjbVussG+sI4lrgJLa7cbHZ19+zZRy9IyMYyvpD/gm4blgha0iOhRxPuxmvLHcNerG2u9q+X18NeJ0bLHxZRpPhOXMzgBDp78LDG1m7NtNW5Poat2JZyxSCTBbs1x3Tk9NUVr8mHLpriFO1ik4EEwIDAQAB</biz_content><success>true</success>'

            # 加载私钥进行签名
            rsa_private_key = load_privatekey(FILETYPE_PEM, open('addons-extra/wxsite/static/rsa_private_key.pem').read())
            rsa_private_sign = sign(rsa_private_key, str_to_sign_by_private, 'sha1')
            rsa_private_sign = base64.b64encode(rsa_private_sign)

            # 拼接返回给支付宝的xml内容
            response_xml = '<?xml version="1.0" encoding="GBK"?><alipay><response>'+str_to_sign_by_private+'</response><sign>'+rsa_private_sign+'</sign><sign_type>RSA</sign_type></alipay>'
            return response_xml.encode('gbk')
        else:
            return 'fail'.encode('gbk')

    @http.route(['/shop/wx/lunch/fromalipay'], type='http', auth="public", website=True)
    def redirect_alipay_oauth(self, **post):
        """
        从支付宝服务窗进入网站的地方，主要向支付宝授权跳转
        """
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        config = pool.get('ir.config_parameter')
        config_obj = pool.get('pos.config')

        desk_id = post.get('desk_id')
        if desk_id:
            config_id = config_obj.browse(cr, SUPERUSER_ID, int(desk_id))
            request.session['company_id'] = config_id.company_id.id
        else:
            values = {
                'company_name':'',
                'error_text':u'登录失败，请联系系统管理员！！',
            }
            return request.website.render("wxsite.error", values)

        ali_appid = '2016030201177117'  # 支付宝APPID
        ali_redirect = config.get_param(cr, uid, 'web.base.url') + '/wxsite/alioauth'  # 支付宝授权后的回调地址，不可包含GET参数
        ali_oauth_url = 'https://openauth.alipay.com/oauth2/publicAppAuthorize.htm?app_id='+ali_appid+'&scope=auth_userinfo&redirect_uri='+urllib.quote(ali_redirect, '')
        return redirect(ali_oauth_url)  # 向支付宝授权跳转

    @http.route(['/wxsite/alioauth'], type='http', auth="public", website=True, csrf=False)
    def ali_oauth(self, **post):
        """
        支付宝用户授权回调地址，在此处根据auth_code来获取支付宝用户信息，进行登录/注册处理
        """
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        ali_code = post['auth_code']  # 授权code，属于GET参数
        _logger.info('----->auth_code:%s'%ali_code)

        """
        根据code获取支付宝用户ID和access_token, Python方法
        """
        sign_params_dic = {
            'app_id': '2016030201177117',  # 支付宝APPID
            'method': 'alipay.system.oauth.token',
            'charset': 'UTF-8',
            'sign_type': 'RSA',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0',
            'grant_type': 'authorization_code',
            'code': ali_code,
        }

        # 待签名参数按key值排序，组合成待加密串
        _, sign_query_str = util.params_filter(sign_params_dic)
        #  sign_query_str = util.sort(sign_params_dic)
        rsa_private_key = RSA.importKey(open('addons-extra/wxsite/static/rsa_private_key.pem','r').read())
        rsa_private_sign=util.sign(sign_query_str, rsa_private_key)
        sign_params_dic['sign'] = rsa_private_sign

        # post到支付宝，获取userId（类似微信的OpenId）
        post_param_query = urllib.urlencode(sign_params_dic)

        httpsClient = httplib.HTTPSConnection('openapi.alipay.com', 443, timeout=6000)
        httpsClient.request('POST', '/gateway.do', post_param_query, {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/html","charset":"utf8"})
        ret_json = httpsClient.getresponse().read()
        ret_dict = json.loads(ret_json.decode('GB2312').encode('UTF-8'))  # 解析json
        ali_userid = ret_dict['alipay_system_oauth_token_response']['user_id']  # 获取userid
        ali_access_token = ret_dict['alipay_system_oauth_token_response']['access_token']  # 获取access_token

        """
        在此处根据支付宝userId判断用户是否已存在数据库中
        """
        users_obj = pool.get('res.users')
        company_id = request.session['company_id']
        login = str(company_id)+ali_userid
        # company_id = 1  # 支付宝授权链接中不能带自定义参数，不能像微信授权那样传递company_id，此处暂默认为1

        wx_user_exists = users_obj.search(cr, SUPERUSER_ID, [('login','=',login),('company_id','=',int(company_id))])
        if not wx_user_exists:
            # 获取用户详细信息如用户名等
            sign_params_dic = {
                'app_id': '2016030201177117',  # 支付宝APPID
                'method': 'alipay.user.userinfo.share',
                'charset': 'UTF-8',
                'sign_type': 'RSA',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 不知为什么，now()总是晚8小时
                'version': '1.0',
                'auth_token': ali_access_token,
            }

            _, sign_query_str = util.params_filter(sign_params_dic)
            rsa_private_key = RSA.importKey(open('addons-extra/wxsite/static/rsa_private_key.pem','r').read())
            rsa_private_sign=util.sign(sign_query_str, rsa_private_key)
            sign_params_dic['sign'] = rsa_private_sign

            # post到支付宝，获取用户名等信息，用于注册
            post_param_query = urllib.urlencode(sign_params_dic)
            httpsClient = httplib.HTTPSConnection('openapi.alipay.com', 443, timeout=6000)
            httpsClient.request('POST', '/gateway.do', post_param_query, {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/html","charset":"utf8"})
            ret_json = httpsClient.getresponse().read()

            ret_dict = json.loads(ret_json.decode('GB2312').encode('UTF-8'))  # 解析json

            if 'nick_name' in ret_dict['alipay_user_userinfo_share_response']:
                ali_username = ret_dict['alipay_user_userinfo_share_response']['nick_name']  # 获取支付宝用户昵称
            else:
                ali_username = ret_dict['alipay_user_userinfo_share_response']['alipay_user_id']

            # 注册用户
            users_obj.create(cr, SUPERUSER_ID, {'login':login,'name':ali_username,'password':'qdodoo','oauth_provider_id':'','company_id':int(company_id),'company_ids':[[6, False, [int(company_id)]]]})

        request.session['alipay_userid'] = ali_userid

        return request.redirect("/login?db=%s&login=%s&key=%s&redirect=%s"%(request.session.db,login, 'qdodoo', 'shop/wx/main'))

    @http.route(['/shop/wx/alipay/pay'], type='http', auth="public", website=True)
    def alipay(self, **post):
        """
        支付宝wap支付
        """
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        #  获取当前公司的名称（根据用户模型获取数据）
        users_obj = pool.get('res.users')
        product_obj = pool.get('product.product')
        taste_obj = pool.get('qdodoo.product.taste')
        session_obj = pool.get('pos.session')
        users = users_obj.browse(cr, SUPERUSER_ID, uid)
        taste_ids = taste_obj.search(cr, SUPERUSER_ID, [])
        tastes = taste_obj.browse(cr, SUPERUSER_ID, taste_ids)
        company_name = users.company_id.name
        company_id = users.company_id.id
        partner_id = users.partner_id.id
        order_obj = pool.get('pos.order')

        if post.get('oid'):
            res_order_id = int(post.get('oid'))
            all_money = float(post.get('money'))
            wx_fix = order_obj.browse(cr, uid, int(res_order_id)).session_id.config_id.en_name
        else:
            session_id = session_obj.search(cr, SUPERUSER_ID, [('config_id.company_id','=',company_id),('state','=','opened')])
            if not session_id:
                values = {
                    'company_name':company_name,
                    'error_text':u'支付宝暂停收款，请联系服务员点餐',
                }
                return request.website.render("wxsite.error", values)
            else:
                #  获取负责人
                session_ids = session_obj.browse(cr, SUPERUSER_ID, session_id[0])
                wx_fix = session_ids.config_id.en_name
                uid_session = session_ids.user_id.id
                car_obj = pool.get('qdodoo.wxsite.car')
                car_ids = car_obj.search(cr, SUPERUSER_ID, [('user_id','=',uid)])
                if car_ids:
                    #  生成销售订单（POS）
                    order_line_obj = pool.get('pos.order.line')
                    res_order_id = order_obj.create(cr, uid_session, {'partner_id':partner_id,'pricelist_id':1,'company_id':company_id})

                    #  获取加入购物车的总金额
                    all_money = 0
                    for key_line in car_obj.browse(cr, SUPERUSER_ID, car_ids):
                        #  根据产品模板id获取产品id
                        product_ids = product_obj.search(cr, SUPERUSER_ID, [('product_tmpl_id','=',key_line.name.id)])
                        all_money += key_line.number * key_line.name.lst_price # 获取总金额
                        #  生成销售单明细
                        order_line_obj.create(cr, uid_session, {'company_id':company_id,'order_id':res_order_id,'product_id':product_ids[0],
                                                                 'qty':key_line.number,'price_unit':key_line.name.lst_price})
                    car_obj.unlink(cr, SUPERUSER_ID, car_ids)
                else:
                    values = {
                        'company_name':company_name,
                        'error_text':u'不能支付空的订单',
                    }
                    return request.website.render("wxsite.error", values)


        config = pool.get('ir.config_parameter')

        # 下面几个变量是支付宝支付相关配置
        alipay_config_dict = {
            'partner': '2088121266041788',  # 合作身份者id，以2088开头的16位纯数字
            'sign_type': 'MD5',  # 签名方式
            'key': '4nzm1m9udzhvi7clurk2k9s6rs0e0cv5',  # 安全检验码，以数字和字母组成的32位字符，如果签名方式设置为“MD5”时，请设置该参数
            'private_key_path': '',  # 商户的私钥（.pem文件）相对路径，如果签名方式设置为“0001”时，请设置该参数
            'ali_public_key_path': '',  # 支付宝公钥（.pem文件）相对路径，如果签名方式设置为“0001”时，请设置该参数
            'input_charset': 'utf-8',  # 字符编码格式 支持 gbk 或 utf-8
            'transport': 'http',  # 访问模式,根据自己的服务器是否支持ssl访问，若支持请选择https；若不支持请选择http
            'cacert': '',  # ca证书路径地址，如果访问模式是https，则填写此处
        }

        """
        组织参数，调用授权接口alipay.wap.trade.create.direct获取授权码token
        """
        oid = str(wx_fix) + str(res_order_id)
        param_dict = {
            'format': 'xml',  # 要求返回格式
            'v': '2.0',  # 返回格式版本
            'req_id': (datetime.datetime.now()+datetime.timedelta(hours=8)).strftime('%Y%m%d%H%M%S'),  # 请求号。使用年月日时分秒，保证每次请求都是唯一
            'notify_url': config.get_param(cr, uid, 'web.base.url') + '/shop/wx/alipay/backnotify',  # 服务器异步通知页面路径
            'call_back_url': config.get_param(cr, uid, 'web.base.url') + '/shop/wx/alipay/frontreturn',  # 页面跳转同步通知页面路径
            'merchant_url': config.get_param(cr, uid, 'web.base.url') + '/shop/wx/alipay/interrupt',  # 操作中断返回地址，用户付款中途退出返回商户的地址。
            'seller_email': 'qdodoo@qdodoo.com',  # 卖家支付宝帐户
            'out_trade_no': oid,  # 商户订单号，此处如果用str(wx_fix)会返回False
            'subject': '订单',  # 订单名称
            'body': str(wx_fix),  # 订单号前缀，期望在后台通知中能原样返回以便解析出订单ID
            'total_fee': str(all_money),  # 付款金额，单位：元
        }

        # 请求业务参数明细
        token_req = '<direct_trade_create_req><notify_url>'+param_dict['notify_url']+'</notify_url><call_back_url>'+param_dict['call_back_url']+'</call_back_url><seller_account_name>'+param_dict['seller_email']+'</seller_account_name><out_trade_no>'+param_dict['out_trade_no']+'</out_trade_no><subject>'+param_dict['subject']+'</subject><total_fee>'+param_dict['total_fee']+'</total_fee><merchant_url>'+param_dict['merchant_url']+'</merchant_url></direct_trade_create_req>'

        # 请求参数组
        req_param_dict = {
            'service': 'alipay.wap.trade.create.direct',
            'partner': alipay_config_dict['partner'],
            'sec_id': alipay_config_dict['sign_type'],
            'format': param_dict['format'],
            'v': param_dict['v'],
            'req_id': param_dict['req_id'],
            'req_data': token_req,
            '_input_charset': alipay_config_dict['input_charset'],
        }

        # 签名
        _, sign_query_str = util.params_filter(req_param_dict)
        alipay_md5_sign = hashlib.md5(sign_query_str + alipay_config_dict['key']).hexdigest()

        # 签名和签名方式加入请求参数中
        req_param_dict['sign'] = alipay_md5_sign
        req_param_dict['sign_type'] = alipay_config_dict['sign_type']

        # 发送post请求，获取token
        alipay_gateway_new = 'http://wappaygw.alipay.com/service/rest.htm?_input_charset='+alipay_config_dict['input_charset']
        post_param_query = urllib.urlencode(req_param_dict)

        http_client = httplib.HTTPConnection('wappaygw.alipay.com', 80, timeout=6000)
        http_client.request('POST', '/service/rest.htm?_input_charset='+alipay_config_dict['input_charset'], post_param_query, {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/html"})
        ret_query = http_client.getresponse().read()
        ret_query = urllib.unquote(ret_query)  # urldecode
        http_client.close()

        """
        支付宝返回的数据格式，一般只需要request_token
        res_data=<?xml version="1.0" encoding="utf-8"?><direct_trade_create_res><request_token>20160304cfe8ccddf25e82eeded3e36d17a1ed1e</request_token></direct_trade_create_res>&service=alipay.wap.trade.create.direct&sec_id=MD5&partner=2088901494850295&req_id=20160304032846&sign=43fb3101321eeb7f928170502e5d1948&v=2.0
        """
        # 截取出其中的request_token
        alipay_request_token = ret_query[ret_query.index('<request_token>')+15:ret_query.index('</request_token>')]

        # 构建请求跳转数组
        form_input_dict ={
            'service': 'alipay.wap.auth.authAndExecute',
            'partner': alipay_config_dict['partner'],
            "sec_id": alipay_config_dict['sign_type'],
            'format': param_dict['format'],
            'v': param_dict['v'],
            'req_id': param_dict['req_id'],
            'req_data': '<auth_and_execute_req><request_token>'+alipay_request_token+'</request_token></auth_and_execute_req>',
            '_input_charset': alipay_config_dict['input_charset'],
        }

        # 再签名
        _, sign_query_str = util.params_filter(form_input_dict)
        alipay_md5_sign = hashlib.md5(sign_query_str + alipay_config_dict['key']).hexdigest()

        # 签名和签名方式等加入请求参数中
        form_input_dict['sign'] = alipay_md5_sign
        form_input_dict['sign_type'] = alipay_config_dict['sign_type']
        form_input_dict['oid'] = res_order_id
        form_input_dict['all_money'] = all_money
        form_input_dict['company_name'] = company_name
        form_input_dict['tastes'] = tastes

        # 调用页面form跳转到支付宝支付
        return request.website.render("wxsite.alipay", form_input_dict)

    @http.route('/shop/wx/alipay/backnotify', type='http', auth='none', methods=['POST'], csrf=False)
    def alipay_backnotify(self, **post):
        """
        支付宝手机网页版支付回调地址，根据支付结果调整本地数据
        """
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        order_obj = pool.get('pos.order')
        payment_obj = pool.get('pos.make.payment')
        config_obj = pool.get('pos.config')
        print_list_obj = pool.get('qdodoo.print.list')
        dict_post_ip = self.pos_id()
        config_id = config_obj.search(cr, SUPERUSER_ID, [('iface_print_via_proxy','=',True)])
        if config_id:
            proxy_ip = config_obj.browse(cr, SUPERUSER_ID, config_id[0]).proxy_ip

        backnotify_sign = post['sign']    # 签名
        return_xml = etree.fromstring(post['notify_data'])

        oid = str(return_xml.find('out_trade_no').text)   # 商户订单号，与发起支付宝支付时填写的out_trade_no一致，可据此处理对应订单
        qid = return_xml.find('trade_no').text    # 交易流水号
        pay_state = return_xml.find('trade_status').text    # 交易状态
        pay_sum = return_xml.find('total_fee').text    # 交易金额
        seller_email = return_xml.find('seller_email').text   # 收款放支付宝帐号
        buyer_email = return_xml.find('buyer_email').text   # 付款方/支付方/用户 支付宝帐号

        # 交易状态成功，则处理
        if pay_state == 'TRADE_SUCCESS' or pay_state == 'TRADE_FINISHED':
            # ----------------------去除前缀获取订单id---------------
            oid = filter(lambda x:x.isdigit(), oid)
            _logger.info('----->order id:%s'%oid)

            pos_obj = order_obj.browse(cr, SUPERUSER_ID, int(oid))
            try:
                # 创建支付记录
                res_id = payment_obj.create(cr, SUPERUSER_ID, {'journal_id':pos_obj.session_id.config_id.journal_ids[0].id,
                                                      'amount':pos_obj.amount_total,'payment_name':u'支付宝wap支付',
                                                      'payment_date':datetime.datetime.now().date()})

                # 支付记录改为已支付
                payment_obj.check(cr, SUPERUSER_ID, [res_id], context={'active_id':pos_obj.id})

                #  组织后台打印数据
                infomation_new = """<receipt align="center" value-thousands-separator="" width="40">
                    <div font="b">
                        <div><pre>订单号 %s</pre></div>
                        <div><pre>%s</pre></div>
                    </div>
                    <div line-ratio="0.6">++++++"""%(pos_obj.name,datetime.datetime.now())
                #  组织前台打印数据
                infomation = """<receipt align="center" value-thousands-separator="" width="40">
                <div font="b">
                        <div>支付宝支付-结账单</div>
                        <div>订单号：%s</div>
                        <div>时间：%s</div>
                        <div>==========================================================</div>
                ++++++<div>产品　　　　　　数量　　　　单价　　　　金额　　　　@@@@@%s@@@@@</div>
                <div>------------------------------------------------------</div>++++++"""%(pos_obj.name,datetime.datetime.now(),pos_obj.session_id.config_id.front_desk)
                for line in pos_obj.lines:
                    infomation_new += """<line size="double-height">
                        <left><pre>%s</pre></left>
                        <right><value>%s</value></right>
                        @@@@@%s@@@@@
                        </line>++++++"""%(line.product_id.name,line.qty,dict_post_ip.get(line.product_id.pos_categ_id.id))
                    product_id_name = line.product_id.name
                    if len(product_id_name) < 8:
                        product_id_name += ('　' * (8-len(product_id_name)))
                    else:
                        product_id_name = product_id_name[:8]
                    product_qty = str(line.qty)
                    if len(product_qty) < 6:
                        product_qty += ('　' * 4)
                    else:
                        product_qty = product_qty[:6]
                    product_list = str(line.product_id.list_price)
                    if len(product_list) < 6:
                        product_list += ('　' * 4)
                    else:
                        product_list = product_list[:6]
                    product_subtotal = str(line.price_subtotal_incl)
                    if len(product_subtotal) < 6:
                        product_subtotal += ('　' * 4)
                    else:
                        product_subtotal = product_subtotal[:6]
                    infomation += """<div>
                    %s
                    %s
                    %s
                    %s
                    @@@@@%s@@@@@
                    </div>++++++"""%(product_id_name,product_qty,product_list,
                    product_subtotal, pos_obj.session_id.config_id.front_desk)
                infomation_new += """</div>
                        <div size="double-height">
                            <left><pre>备注：%s号桌 %s</pre></left>
                        </div>
                        </receipt>"""%(pos_obj.customer_count, pos_obj.note)
                amount_total = str(pos_obj.amount_total)
                if len(amount_total) < 6:
                    amount_total += ('　' * 4)
                else:
                    amount_total = amount_total[:6]
                note = u'号桌:'+str(pos_obj.customer_count)+'　　备注：'+ pos_obj.note
                infomation += """
                    <div>------------------------------------------------------</div>
                    <div size="double-height">
                        合计　　　　　　　　　　　　　　　　　%s
                    </div>
                    <div>------------------------------------------------------</div>
                    <div size="double-height">
                        %s
                    </div>
                    <div>==========================================================</div>
                    <div>%s</div>
                    <div>电话：%s</div>
                    <div>%s</div>
                    </div>
                </receipt>"""%(amount_total, note, pos_obj.company_id.name, pos_obj.company_id.phone, pos_obj.company_id.website)
                print_list_obj.create(cr, SUPERUSER_ID, {'name':infomation,'is_print':False})
                print_list_obj.create(cr, SUPERUSER_ID, {'name':infomation_new,'is_print':False})
            except Exception,e:
                _logger.info('ERROR------------------------:%s'%e)

            order_obj.write(cr, SUPERUSER_ID, [int(oid)], {'is_payment':True})

            # 处理订单
            order_obj.signal_workflow(cr, SUPERUSER_ID, [int(oid)], 'paid')

            return 'success'
        else:
            return 'success'


    @http.route('/shop/wx/alipay/frontreturn', type='http', auth='none', methods=['GET'], csrf=False)
    def alipay_frontreturn(self, **post):
        """
        支付宝手机网页版支付前台回跳，即用户支付完成后点击“返回商家”所到的地址
        因为对支付的处理主要在异步回调中执行，因此此处不再进行重复处理，直接跳转到订单页面
        """

        return redirect('/shop/wx/order')

    @http.route('/shop/wx/alipay/interrupt', type='http', auth='none', methods=['GET'], csrf=False)
    def alipay_interrupt(self, **post):
        """
        支付宝手机网页版支付中断会通知的地址，基本不用什么处理
        """

        return 'success'


