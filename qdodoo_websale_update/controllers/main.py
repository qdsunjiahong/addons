# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp.addons.website_sale.controllers import main
from  openerp.addons.website_sale.controllers.main import *
from openerp import http
from openerp.http import request

main.PPG = 30


class qdodooo_website_update(website_sale):
    """
        Taylor 原创自己的模块
        获取全部有数据的产品
    """

    @http.route(['/shop/bat/cart'], type='http', auth="public", methods=['POST'], website=True)
    def add_all_product(self, add_qty=1, set_qty=0, **kw):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # product_obj = pool['product.product']
        partner = pool.get('res.users').browse(cr, SUPERUSER_ID, uid, context=context).partner_id
        print 'user ref partner is ===', int(partner)
        # 读取当前客户的出库库位
        output_warehouse = pool.get('res.partner').browse(cr, uid, int(partner)).out_stock
        sale_order = ""
        for key, value in kw.items():
            if int(value) > 0:
                sql = "SELECT id   FROM product_product where product_tmpl_id=%s" % key
                cr.execute(sql)
                product_id = cr.fetchall()[0]
                sale_order = request.website.sale_get_order(force_create=1)
                print 'sale_order is =============',sale_order
                sale_order._cart_update(product_id=int(product_id[0]),add_qty=float(value),set_qty=float(set_qty))
        print 'finally sale_order is ==',int(sale_order)
        if output_warehouse:
             print 'output_warehouse is ===', int(output_warehouse)
             pool.get('sale.order').write(cr, SUPERUSER_ID, int(sale_order), {'warehouse_id': int(output_warehouse)})
        return request.redirect("/shop/cart")
        # #得到销售订单
        # request.website.sale_get_order(force_create=1)._cart_update(product_id=int(product_id), add_qty=float(add_qty), set_qty=float(set_qty))
        # return request.redirect("/shop/cart")

    # 检测到路径中包含/shop
    @http.route(['/shop',
                 '/shop/page/<int:page>',
                 '/shop/category/<model("product.public.category"):category>',
                 '/shop/category/<model("product.public.category"):category>/page/<int:page>'
                 ], type='http', auth="public", website=True)
    # 用shop方法处理URL请求 页面数为0 分类为空  搜索为空
    def shop(self, page=0, category=None, search='', **post):
        # 得到网页相关对象
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # print '====================================shop'
        # 得到搜索区间
        domain = request.website.sale_product_domain()

        # 如果存在搜索
        if search:
            # 遍历每个搜索条件
            for srch in search.split(" "):
                # 把搜索条件转化为 oa代码 区间集合
                domain += ['|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                           ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]
        #####自己定义保存之前的过滤条件
        cata_domain = domain
        # 来查看一下我们的搜索条件
        # 如果有类别
        if category:
            # 条件还要添加 判断类别是它的父级
            domain += [('public_categ_ids', 'child_of', int(category))]
        # 属性列表 什么鬼？ 貌似得到了attrib 这个属性
        attrib_list = request.httprequest.args.getlist('attrib')
        # 属性值
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        # 属性列表
        attrib_set = set([v[1] for v in attrib_values])

        # 如果属性值不为空
        if attrib_values:
            attrib = None
            # 创建空列表
            ids = []
            # 遍历 属性值
            for value in attrib_values:
                # 如果没有属性值
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]
        # 调用查询Url
        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list)
        # 如果挡墙网页中没有的到pricelist
        if not context.get('pricelist'):
            # pricelist 得到价格表 例如product.pricelist(25,)
            pricelist = self.get_pricelist()
            # 将pricelist写入字典
            context['pricelist'] = int(pricelist)
        else:
            # 存在 就在product.pricelist 查询出相应的价格列表 价格表
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)
        # product_obj 得到产品模板

        product_obj = pool.get('product.template')
        # print  "context['pricelist']", context['pricelist']
        # 搜索产品价格表中的产品
        pricelist_version_ids = pool.get('product.pricelist.version').search(cr, uid, [
            ('pricelist_id', '=', context['pricelist'])], context=context)
        # print 'pricelist_version_ids',pricelist_version_ids
        pricelist_procuct_item_ids = pool.get('product.pricelist.item').search(cr, uid, [
            ('price_version_id', 'in', pricelist_version_ids)], context=context)
        # print  'pricelist_procuct_item_ids',pricelist_procuct_item_ids
        pricelist_procuct_ids = []
        for search_id in pricelist_procuct_item_ids:
            product_item = pool.get('product.pricelist.item').browse(cr, uid, search_id, context=context)[0]
            # print 'product_item',product_item
            # print 'pricelist_procuct_ids.product_id',product_item.product_id.id
            # 如果存在产品类别
            if product_item.categ_id:
                # print "============================="
                # print 'product_item.categ_id is ==', product_item.categ_id
                product_ids = pool.get('product.product').search(cr, uid,
                                                                 [('categ_id', 'child_of', product_item.categ_id.id)])
                temp_ids = pool.get('product.product').browse(cr, uid, product_ids)
                # print 'product_ids is ========', product_ids
                for temp_id in temp_ids:
                    # print  'temp_id is ===',temp_id.product_tmpl_id.id
                    if temp_id.product_tmpl_id.id not in pricelist_procuct_ids:
                        pricelist_procuct_ids.append(temp_id.product_tmpl_id.id)
                        # cr.execute("SELECT product_tmpl_id   FROM product_product where categ_id.id %s" % product_item.categ_id)
                        # pricelist_procuct_ids.append(cr.fetchall())
            if product_item.product_id.id:
                cr.execute("SELECT product_tmpl_id   FROM product_product where id=%s" % product_item.product_id.id)
                all_id = cr.fetchall()
                for sql_id in all_id:
                    if sql_id not in pricelist_procuct_ids:
                        print  'sql_id is ', sql_id[0]
                        pricelist_procuct_ids.append(sql_id[0])
            # 如果又没有类别 又没有产品
            if not product_item.product_id.id and not product_item.categ_id:
                cr.execute("SELECT product_tmpl_id   FROM product_product")
                pricelist_procuct_ids = cr.fetchall()
                # print 'else pricelist_procuct_ids:',pricelist_procuct_ids
                break
        # print 'finally pricelist_procuct_ids is ===',pricelist_procuct_ids
        domain += [('id', 'in', pricelist_procuct_ids)]


        # 更改查询数据
        # print 'finally if domain  is', domain
        url = "/shop"
        # product_count 为过滤产品总数
        product_count = product_obj.search_count(cr, uid, domain, context=context)
        # 如果有过滤条件
        if search:
            post["search"] = search
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            # 属性 为attrib_list
            post['attrib'] = attrib_list
        # 分页信息
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)

        # 产品列表  产品模板搜索 PPG 当前页面产品数量    过滤pager['offset'] 这些数量   跟读 website_published 排序
        # print 'uid', uid, 'limit', PPG, 'offset', pager['offset']
        product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'],
                                         order='website_published desc, website_sequence desc', context=context)
        # print 'product_ids', product_ids
        # 产品 查询对应的产品书
        products = product_obj.browse(cr, uid, product_ids, context=context)
        # print 'products', products
        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)

        # 计算出产品类别 方便在页面显示
        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        cata_data = []
        cata_domain += [('id', 'in', pricelist_procuct_ids)]
        for cate_id in category_ids:
            this_domain = [('public_categ_ids', 'child_of', int(cate_id))]
            product_ids = product_obj.search(cr, uid, this_domain + cata_domain, limit=PPG, offset=pager['offset'],
                                             order='website_published desc, website_sequence desc', context=context)
            if product_ids:
                if cate_id not in cata_data:
                    cata_data.append(cate_id)
        # print  'cate_date is=============', cata_data
        categs = category_obj.browse(cr, uid, cata_data, context=context)

        attributes_obj = request.registry['product.attribute']
        attributes_ids = attributes_obj.search(cr, uid, [], context=context)
        attributes = attributes_obj.browse(cr, uid, attributes_ids, context=context)

        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price,
                                                                       context=context)

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'bins': table_compute().process(products),
            'rows': PPR,
            'styles': styles,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib', i) for i in attribs]),
        }
        # print "======================shop products", values.get(products)
        return request.website.render("website_sale.products", values)

    def checkout_values(self, data=None):
        print '===============================checkout_values'
        #得到基本的对象和基本的数据
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        orm_partner = registry.get('res.partner')
        orm_user = registry.get('res.users')
        orm_country = registry.get('res.country')
        state_orm = registry.get('res.country.state')

        #搜索出哪个国家
        country_ids = orm_country.search(cr, SUPERUSER_ID, [], context=context)
        #得到国家数据
        countries = orm_country.browse(cr, SUPERUSER_ID, country_ids, context)
        print 'countries',countries
        #搜索出当前国家的状态？  啥状态？？？
        states_ids = state_orm.search(cr, SUPERUSER_ID, [], context=context)
        #得到状态值
        states = state_orm.browse(cr, SUPERUSER_ID, states_ids, context)
        print 'states',states
        #得到当前用户的供应商
        partner = orm_user.browse(cr, SUPERUSER_ID, request.uid, context).partner_id
        print 'partner',partner

        #初始化订单
        order = None

        #初始化物流单 等一系列数据
        shipping_id = None
        shipping_ids = []
        checkout = {}

        print '22222222222 checkout is all value ======',checkout
        #如果没有
        if not data:
            #如果当前的用户不为  当前站点所显示的id
            if request.uid != request.website.user_id.id:
                checkout.update( self.checkout_parse("billing", partner) )
                shipping_ids = orm_partner.search(cr, SUPERUSER_ID, [("parent_id", "=", partner.id), ('type', "=", 'delivery')], context=context)
                # #print '3444444444444444444444444444444444444',checkout.get('city').name
                if checkout.get('city'):
                    checkout['city_id']=checkout.get('city').id
                    checkout['city']=checkout.get('city').name

                print '3333333333333 checkout is all value ======',checkout
            else:
                order = request.website.sale_get_order(force_create=1, context=context)
                if order.partner_id:
                    domain = [("partner_id", "=", order.partner_id.id)]
                    user_ids = request.registry['res.users'].search(cr, SUPERUSER_ID, domain, context=dict(context or {}, active_test=False))
                    if not user_ids or request.website.user_id.id not in user_ids:
                        checkout.update( self.checkout_parse("billing", order.partner_id) )

        else:
            checkout = self.checkout_parse('billing', data)
            try:
                shipping_id = int(data["shipping_id"])
            except ValueError:
                pass
            if shipping_id == -1:
                checkout.update(self.checkout_parse('shipping', data))

        if shipping_id is None:
            if not order:
                order = request.website.sale_get_order(context=context)
            if order and order.partner_shipping_id:
                shipping_id = order.partner_shipping_id.id

        shipping_ids = list(set(shipping_ids) - set([partner.id]))
        print '111111111111111111111111111checkout is all value ======',checkout
        if shipping_id == partner.id:
            shipping_id = 0
        elif shipping_id > 0 and shipping_id not in shipping_ids:
            shipping_ids.append(shipping_id)
        elif shipping_id is None and shipping_ids:
            shipping_id = shipping_ids[0]

        ctx = dict(context, show_address=1)
        shippings = []
        if shipping_ids:
            shippings = shipping_ids and orm_partner.browse(cr, SUPERUSER_ID, list(shipping_ids), ctx) or []
        if shipping_id > 0:
            shipping = orm_partner.browse(cr, SUPERUSER_ID, shipping_id, ctx)
            checkout.update( self.checkout_parse("shipping", shipping) )

        checkout['shipping_id'] = shipping_id

        # Default search by user country
        if not checkout.get('country_id'):
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                country_ids = request.registry.get('res.country').search(cr, uid, [('code', '=', country_code)], context=context)
                if country_ids:
                    checkout['country_id'] = country_ids[0]
        print 'checkout is all value ======',checkout
        values = {
            'countries': countries,
            'states': states,
            'checkout': checkout,
            'shipping_id': partner.id != shipping_id and shipping_id or 0,
            'shippings': shippings,
            'error': {},
            'has_check_vat': hasattr(registry['res.partner'], 'check_vat')
        }

        return values

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
        print '===============================confirm_order'
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        #得到销售订单
        order = request.website.sale_get_order(context=context)
        #没有销售订单就返回销售列表
        if not order:
            return request.redirect("/shop")

        #监测是否需要重定向 需要则重定向
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        print "confirm_order post is===========",post

        if post.get('city'):
            city_id=registry.get('hm.city').search(cr , SUPERUSER_ID ,[('name','=',post.get('city'))])
            if city_id:
                post['city']=city_id[0]
            else:
                print '城市有误 不给处理'
                # return
        #得到全局变量
        values = self.checkout_values(post)

        values["error"] = self.checkout_form_validate(values["checkout"])
        if values["error"]:
            return request.website.render("website_sale.checkout", values)

        self.checkout_form_save(values["checkout"])

        request.session['sale_last_order_id'] = order.id

        request.website.sale_get_order(update_pricelist=True, context=context)

        return request.redirect("/shop/payment")

#貌似是最终付款
    @http.route('/shop/payment/validate', type='http', auth="public", website=True)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :
         - UDPATE ME
        """
        print '======================/shop/payment/validate start'
        #得到常用的几个字段和值
        cr, uid, context = request.cr, request.uid, request.context
        #初始化email
        email_act = None
        #得到销售对象
        sale_order_obj = request.registry['sale.order']

        #交易单号为空
        if transaction_id is None:
            #得到相应的订单号
            tx = request.website.sale_get_transaction()
        else:
            #不然手动查询出来
            tx = request.registry['payment.transaction'].browse(cr, uid, transaction_id, context=context)

        #如果没有销售订单
        if sale_order_id is None:
            #调用方法得到销售订单
            order = request.website.sale_get_order(context=context)
        else:
            #查询出相应的销售订单
            order = request.registry['sale.order'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)
            #还是在判断下 当前订单号 和缓存中的是否一致
            assert order.id == request.session.get('sale_last_order_id')
        #如果 没有订单  跳转到销售页面
        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')
        #没有订单的数量  或者tx的状态 在付款 或完成
        if (not order.amount_total and not tx) or tx.state in ['pending', 'done']:
            if (not order.amount_total and not tx):
                #付款交易确认耽误订单
                # Orders are confirmed by payment transactions, but there is none for free orders,
                # (e.g. free events), so confirm immediately
                order.action_button_confirm()
            # send by email
            #邮件act为销售订单 生成报价单
            email_act = sale_order_obj.action_quotation_send(cr, SUPERUSER_ID, [order.id], context=request.context)
        #当状态为取消
        elif tx and tx.state == 'cancel':
            # cancel the quotation
            sale_order_obj.action_cancel(cr, SUPERUSER_ID, [order.id], context=request.context)

        # send the email
        #
        if email_act and email_act.get('context'):
            composer_obj = request.registry['mail.compose.message']
            composer_values = {}
            email_ctx = email_act['context']
            template_values = [
                email_ctx.get('default_template_id'),
                email_ctx.get('default_composition_mode'),
                email_ctx.get('default_model'),
                email_ctx.get('default_res_id'),
            ]
            print 'template_values value is=========',template_values
            composer_values.update(composer_obj.onchange_template_id(cr, SUPERUSER_ID, None, *template_values, context=context).get('value', {}))

            if not composer_values.get('email_from') and uid == request.website.user_id.id:
                composer_values['email_from'] = request.website.user_id.company_id.email
            for key in ['attachment_ids', 'partner_ids']:
                if composer_values.get(key):
                    composer_values[key] = [(6, 0, composer_values[key])]
            composer_id = composer_obj.create(cr, SUPERUSER_ID, composer_values, context=email_ctx)
            composer_obj.send_mail(cr, SUPERUSER_ID, [composer_id], context=email_ctx)

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset(context=context)

        return request.redirect('/shop/confirmation')
