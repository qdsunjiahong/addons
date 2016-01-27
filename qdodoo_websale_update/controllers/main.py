# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from  openerp.addons.website_sale.controllers.main import *
from openerp import http
from openerp.http import request
from  openerp.tools.translate import GettextAlias
from openerp.exceptions import except_orm
import  datetime
_ = GettextAlias()


class qdodoo_pageer(table_compute):
    PPG = 150

    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= PPR:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break
            for x in range(PPR):
                self.table[posy + y].setdefault(x, None)
        return res

    def process(self, products):
        # 最小值
        minpos = 0
        # 数量
        index = 0
        # 最大值
        maxy = 0
        # 遍历产品
        for p in products:
            x = min(max(p.website_size_x, 1), PPR)
            y = min(max(p.website_size_y, 1), PPR)
            if index >= PPG:
                x = y = 1

            pos = minpos
            while not self._check_place(pos % PPR, pos / PPR, x, y):
                pos += 1

            if index >= PPG and ((pos + 1.0) / PPR) > maxy:
                break

            if x == 1 and y == 1:  # simple heuristic for CPU optimization
                minpos = pos / PPR

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos / PPR) + y2][(pos % PPR) + x2] = False
            self.table[pos / PPR][pos % PPR] = {
                'product': p, 'x': x, 'y': y,
                'class': " ".join(map(lambda x: x.html_class or '', p.website_style_ids))
            }
            if index <= PPG:
                maxy = max(maxy, y + (pos / PPR))
            index += 1

        # Format table according to HTML needs
        rows = self.table.items()
        rows.sort()
        rows = map(lambda x: x[1], rows)
        for col in range(len(rows)):
            cols = rows[col].items()
            cols.sort()
            x += len(cols)
            rows[col] = [c for c in map(lambda x: x[1], cols) if c != False]
        return rows

        # TODO keep with input type hidden

class qdodooo_website_update(website_sale):
    """
        Taylor 原创自己的模块
        获取全部有数据的产品
    """

    @http.route(['/shop/bat/cart'], type='http', auth="public", methods=['POST'], website=True)
    def add_all_product(self, add_qty=1, set_qty=0,**kw):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # 判断产品赠品问题
        # 获取选择的产品列表
        template_ids = []
        for key in kw:
            template_ids.append(int(key))
        # 获取产品和赠品之间的id关系{产品：【赠品模型】}
        gifts_dict = {}
        template_obj = pool.get('product.template')
        for line in template_obj.browse(cr, uid, template_ids):
            if line.is_gifts and line.gifts_ids:
                gifts_dict[line.id] = []
                for key_line in line.gifts_ids:
                    gifts_dict[line.id].append(key_line)
        # 获取赠品的数量
        gifts_num = {}
        for key, value in kw.items():
            if int(key) in gifts_dict:
                for line_val in gifts_dict[int(key)]:
                    if line_val.name.id in gifts_num:
                        gifts_num[line_val.name.id] += line_val.number * float(value)
                    else:
                        gifts_num[line_val.name.id] = line_val.number * float(value)
        # 判断赠品的数量是否超过
        for key, value in kw.items():
            if int(key) in gifts_num:
                if float(value) > gifts_num[int(key)]:
                    return "<html><head><body><p>赠品数量不能大于产品数量</p><a href='/shop/cart'>返回购物车</a></body></head></html>"
        if not context.get('pricelist'):
            # pricelist 得到价格表 例如product.pricelist(25,)
            pricelist = self.get_pricelist()
            # 将pricelist写入字典
            context['pricelist'] = int(pricelist)
        else:
            # 存在 就在product.pricelist 查询出相应的价格列表 价格表
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)
        partner = pool.get('res.users').browse(cr, uid, uid, context=context).partner_id
        # 读取当前客户的出库库位
        output_warehouse = pool.get('res.partner').browse(cr, uid, int(partner)).out_stock
        sale_order = ""
        for key, value in kw.items():
            if int(value) > 0:
                if key !='category':
                    sql = "SELECT id FROM product_product where product_tmpl_id=%s" % key
                    cr.execute(sql)
                    product_id = cr.fetchall()[0]
                    sale_order = request.website.sale_get_order(force_create=1)
                    sale_order._cart_update(product_id=int(product_id[0]), add_qty=float(value), set_qty=float(set_qty))
        if output_warehouse:
            pool.get('sale.order').write(cr, uid, int(sale_order), {'warehouse_id': int(output_warehouse)})
        return request.redirect("/shop/cart")


    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        order = request.website.sale_get_order()
        if order:
            from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
        else:
            compute_currency = lambda price: price
        multiple=request.session.get('taylor_session')
        values = {
            'multiple':multiple,
            'order': order,
            'compute_currency': compute_currency,
            'suggested_products': [],
        }
        if order:
            _order = order
            if not context.get('pricelist'):
                _order = order.with_context(pricelist=order.pricelist_id.id)
            values['suggested_products'] = _order._cart_accessories()

        return request.website.render("website_sale.cart", values)

    # 检测到路径中包含/shop
    @http.route(['/shop',
                 '/shop/page/<int:page>',
                 '/shop/category/<model("product.public.category"):category>',
                 '/shop/category/<model("product.public.category"):category>/page/<int:page>'
                 ], type='http', auth="public", website=True)
    # 用shop方法处理URL请求 页面数为0 分类为空  搜索为空
    def shop(self, page=0, category=None, search='', **post):
        PPG = 150
        # 得到网页相关对象
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # 得到搜索区间
        domain = request.website.sale_product_domain()
        #得到库位的id
        # 如果存在搜索
        if search:
            # 遍历每个搜索条件
            for srch in search.split(" "):
                # 把搜索条件转化为 oa代码 区间集合
                domain += ['|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                           ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

        #自己定义保存之前的过滤条件
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
        # 搜索产品价格表中的产品
        pricelist_version_ids = pool.get('product.pricelist.version').search(cr, uid, [
            ('pricelist_id', '=', pricelist.id)], context=context)
        version=""
        #取得生效的价格表
        lst = {}
        for version_id in pool.get('product.pricelist.version').browse(cr ,uid ,pricelist_version_ids,context=context):
            if (version_id.date_start is False) or (version_id.date_start <= datetime.datetime.now()):
                lst[version_id] = version_id.date_end
        a = ''
        for line_key,line_value in lst.items():
            if line_key.date_end >= datetime.datetime.now().strftime('%Y-%m-%d'):
                if not version:
                    a = line_value
                    version = line_key.id
                else:
                    if a > line_value or not a:
                        version = line_key.id
            if (line_key.date_end is False) and not version:
                a = line_value
                version = line_key.id
        #查询到相应的价格表
        pricelist_procuct_item_ids = pool.get('product.pricelist.item').search(cr, uid, [
            ('price_version_id', '=', version)])
        pricelist_procuct_ids = []
        key={}
        product_item_dict={}
        #搜索出相应的价格表明细
        i=0
        product_list_item=pool.get('product.pricelist.item').browse(cr, uid, pricelist_procuct_item_ids, context=context)
        # 循环获取的价格表版本明细
        for product_item in product_list_item:
            #查询出相应的行
            i=i+1
            if not product_item.multipl:
                product_item_dict[product_item.id]=1

            #如果存在产品模板
            if product_item.product_tmpl_id:
                # 产品模板如果不存在于pricelist_procuct_ids中，将模板id加入到其中
                if product_item.product_tmpl_id.id not in pricelist_procuct_ids:
                    pricelist_procuct_ids.append(product_item.product_tmpl_id.id)
                    # key{产品模板id：倍数}
                    key[product_item.product_tmpl_id.id]=product_item.multipl
            if product_item.categ_id:
                product_ids = product_obj.search(cr, uid,[('categ_id', 'child_of', product_item.categ_id.id)])
                temp_ids = product_obj.browse(cr, uid, product_ids)
                for temp_id in temp_ids:
                    if temp_id.product_tmpl_id.id not in pricelist_procuct_ids:
                        pricelist_procuct_ids.append(temp_id.product_tmpl_id.id)
                        key[temp_id.product_tmpl_id.id]=product_item.multipl
            if  product_item.product_id:
                #先查询出相应的产品模板id
                cr.execute("SELECT product_tmpl_id   FROM product_product where id=%s" % product_item.product_id.id)
                all_id = cr.fetchall()
                for sql_id in all_id:
                    if sql_id not in pricelist_procuct_ids:
                        pricelist_procuct_ids.append(sql_id[0])
                        key[sql_id[0]]=product_item.multipl
            if not product_item.product_id.id and not product_item.categ_id and not product_item.product_tmpl_id :
                cr.execute("SELECT id   FROM product_template")
                list=[]
                for i in cr.fetchall():
                    list.append(i[0])
                pricelist_procuct_ids=list
                for i in pricelist_procuct_ids:
                    key[i]=product_item.multipl
                break
        request.session['taylor_session']=key
        # domain += [('id', 'in', pricelist_procuct_ids)]


        # 更改查询数据
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
        product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'],
                                         order='website_published desc, website_sequence desc', context=context)
        # 产品 查询对应的产品书
        product_num = {}
        for key_line, value_line in self.get_local_num_dict(product_ids).items():
            if value_line > 2000:
                product_num[key_line] = '充足'
            elif 2000 > value_line > 1000:
                product_num[key_line] = '紧张'
            elif value_line <= 0:
                product_ids.remove(key_line)
            else:
                product_num[key_line] = str(value_line)
        products = product_obj.browse(cr, uid, product_ids, context=context)
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
        # if not cata_data:
        #     categs
        if not request.session.get('taylot_categs'):
            request.session['taylot_categs'] = cata_data
        # #     self.TAY_CATEGORY = category_obj.browse(cr, uid, cata_data, context=context)
        if  request.session['taylot_categs']:
            categs = category_obj.browse(cr, uid, request.session.get('taylot_categs'), context=context)
        else:
            categs=category_obj.browse(cr, uid, [], context=context)
        if request.session.get('taylot_categs'):
            tay_cate=request.session.get('taylot_categs')

        attributes_obj = request.registry['product.attribute']
        attributes_ids = attributes_obj.search(cr, uid, [], context=context)
        attributes = attributes_obj.browse(cr, uid, attributes_ids, context=context)
        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price,
                                                                       context=context)

        values = {
            'product_num':product_num,
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'key':key,
            'bins': table_compute().process(products),
            'rows': PPR,
            'styles': styles,
            # 'categories': request.session.get('taylot_categs'),
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib', i) for i in attribs]),
        }
        return request.website.render("website_sale.products", values)

    def get_local_num_dict(self, template_ids):
        '''
        通过产品模板id和 当前UID查询出当前门店对应的库位
        返回库位中每个产品模板对应数量的字典
        1.通过产品ID找到对应的产品
        2.在QUant中搜索所有
        :param template_id: 产品模板列表
        :return:  产品模板 对应的产品数量
        '''
        #先设定常用变量
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        #查询出当前客户
        partner = pool.get('res.users').browse(cr, uid, uid, context=context)
        product_obj=pool.get('product.product')
        quant_obj=pool.get('stock.quant')
        move_obj=pool.get('stock.move')
        if not partner.location_id:
            raise except_orm(_('Warning!'),_('当前没有有效的库位信息，请检查客户资料是否正确！'))
        # 获取出库库位
        local_id=partner.location_id.id
        re_dict={}
        # 查询组合品模板id
        mrp_dict = []
        mrp_obj = pool.get('mrp.bom')
        mrp_ids = mrp_obj.search(cr, uid, [('type','=','phantom')])
        for mrp_id in mrp_obj.browse(cr, uid, mrp_ids):
            mrp_dict.append(mrp_id.product_tmpl_id.id)

        # 获取产品的库存数量
        quant_product_dict = {}
        quant_ids = quant_obj.search(cr, uid, [('location_id','=',local_id)])
        for quant in quant_obj.browse(cr, uid, quant_ids):
            quant_product_dict[quant.product_id.id] = quant.qty

        #先查询出产品模版对应的产品
        for temp_id in template_ids:
            for product_id in product_obj.search(cr ,uid ,[('product_tmpl_id','=',temp_id)]):
                #根据产品ID查询出产quant中的数量
                if product_id in quant_product_dict:
                    if temp_id in re_dict:
                        re_dict[temp_id] += quant_product_dict.get(product_id)
                    else:
                        re_dict[temp_id] = quant_product_dict.get(product_id)

        # 获取被占用的库存
        quant_dict = {}
        move_ids = move_obj.search(cr, uid, [('state','in',('confirmed','assigned')),('location_id','=',local_id)])
        for move_id in move_obj.browse(cr, uid, move_ids):
            if move_id.reserved_quant_ids:
                for quant_id in move_id.reserved_quant_ids:
                    if quant_id.product_id.product_tmpl_id.id in quant_dict:
                        quant_dict[quant_id.product_id.product_tmpl_id.id] += quant_id.qty
                    else:
                        quant_dict[quant_id.product_id.product_tmpl_id.id] = quant_id.qty
        for key_line, values_line in re_dict.items():
            if key_line in mrp_dict:
                re_dict[key_line] = 3000
            else:
                re_dict[key_line] = values_line - quant_dict.get(key_line,0.0)
        return re_dict

    def checkout_values(self, data=None):
        # 得到基本的对象和基本的数据
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        orm_partner = registry.get('res.partner')
        orm_user = registry.get('res.users')
        orm_country = registry.get('res.country')
        state_orm = registry.get('res.country.state')

        # 搜索出哪个国家
        country_ids = orm_country.search(cr, uid, [], context=context)
        # 得到国家数据
        countries = orm_country.browse(cr, uid, country_ids, context)
        # 搜索出当前国家的状态？  啥状态？？？
        states_ids = state_orm.search(cr, uid, [], context=context)
        # 得到状态值
        states = state_orm.browse(cr, uid, states_ids, context)
        # 得到当前用户的供应商
        partner = orm_user.browse(cr, uid, request.uid, context).partner_id

        # 初始化订单
        order = None

        # 初始化物流单 等一系列数据
        shipping_id = None
        shipping_ids = []
        checkout = {}

        # 如果没有
        if not data:
            # 如果当前的用户不为  当前站点所显示的id
            if request.uid != request.website.user_id.id:
                checkout.update(self.checkout_parse("billing", partner))
                shipping_ids = orm_partner.search(cr, uid,
                                                  [("parent_id", "=", partner.id), ('type', "=", 'delivery')],
                                                  context=context)
                if checkout.get('city'):
                    # checkout['city_id'] = checkout.get('city').id
                    checkout['city'] = checkout.get('city').id
            else:
                order = request.website.sale_get_order(force_create=1, context=context)
                if order.partner_id:
                    domain = [("partner_id", "=", order.partner_id.id)]
                    user_ids = request.registry['res.users'].search(cr, uid, domain,
                                                                    context=dict(context or {}, active_test=False))
                    if not user_ids or request.website.user_id.id not in user_ids:
                        checkout.update(self.checkout_parse("billing", order.partner_id))

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
        if shipping_id == partner.id:
            shipping_id = 0
        elif shipping_id > 0 and shipping_id not in shipping_ids:
            shipping_ids.append(shipping_id)
        elif shipping_id is None and shipping_ids:
            shipping_id = shipping_ids[0]

        ctx = dict(context, show_address=1)
        shippings = []
        if shipping_ids:
            shippings = shipping_ids and orm_partner.browse(cr, uid, list(shipping_ids), ctx) or []
        if shipping_id > 0:
            shipping = orm_partner.browse(cr, uid, shipping_id, ctx)
            checkout.update(self.checkout_parse("shipping", shipping))

        checkout['shipping_id'] = shipping_id

        # Default search by user country
        if not checkout.get('country_id'):
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                country_ids = request.registry.get('res.country').search(cr, uid, [('code', '=', country_code)],
                                                                         context=context)
                if country_ids:
                    checkout['country_id'] = country_ids[0]
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

    # 去掉地址页面
    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        order = request.website.sale_get_order(force_create=1, context=context)
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
        values = self.checkout_values()

        return request.redirect("/shop/confirm_order")
        # return request.website.render("website_sale.checkout", values)

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        # 得到销售订单
        order = request.website.sale_get_order(context=context)
        promotion_obj = request.registry['qdodoo.promotion']
        users_obj = request.registry['res.users']
        # 没有销售订单就返回销售列表
        if not order:
            return request.redirect("/shop")

        # 监测是否需要重定向 需要则重定向
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
        if post.get('city'):
            city_id = registry.get('hm.city').search(cr, uid, [('name', '=', post.get('city'))])
            if city_id:
                post['city'] = city_id[0]
            else:
                return
        # 得到全局变量
        values = self.checkout_values(post)

        values["error"] = self.checkout_form_validate(values["checkout"])
        if values["error"]:
            return request.website.render("website_sale.checkout", values)

        self.checkout_form_save(values["checkout"])

        request.session['sale_last_order_id'] = order.id

        request.website.sale_get_order(update_pricelist=True, context=context)
        # 判断赠品是否合适
        # 获取产品模板id和数量字典
        # 获取产品模板对应产品字典
        template_dict = {}
        template_lst = []
        product = {}
        for line in order.order_line:
            if line.product_id.product_tmpl_id.is_gifts:
                template_lst.append(line.product_id.product_tmpl_id.id)
            template_dict[line.product_id.product_tmpl_id.id] = line.product_uom_qty
            product[line.product_id.product_tmpl_id.id] = line.product_id.id
        # 获取产品和赠品之间的关系
        gifts_dict = {}
        template_obj = registry.get('product.template')
        line_obj = registry.get('sale.order.line')
        for line in template_obj.browse(cr, uid, template_lst):
            if line.is_gifts and line.gifts_ids:
                gifts_dict[line.id] = []
                for key_line in line.gifts_ids:
                    gifts_dict[line.id].append(key_line)
        # 获取赠品的数量
        gifts_num = {}
        for key, value in template_dict.items():
            if key in gifts_dict:
                for line_val in gifts_dict[key]:
                    if line_val.name.id in gifts_num:
                        gifts_num[line_val.name.id] += line_val.number * float(value)
                    else:
                        gifts_num[line_val.name.id] = line_val.number * float(value)
        multiple=request.session.get('taylor_session')
        # 判断赠品的数量是否超过
        for key, value in template_dict.items():
            line_ids = line_obj.search(cr, uid, [('product_id','=',product.get(key)),('order_id','=',order.id)])
            line_obj_ids = line_obj.browse(cr, uid, line_ids[0])
            if key in gifts_num:
                line_obj.write(cr, uid, line_ids, {'price_unit':0.0})
                if value > gifts_num[key]:
                    return "<html><head><body><p>赠品数量不能大于产品数量</p><a href='/shop/cart'>返回购物车</a></body></head></html>"
            line_obj.write(cr, uid, line_ids, {'multiple_number':line_obj_ids.product_uom_qty*multiple.get(key)})
        promotion_obj = registry.get('qdodoo.promotion')
        line_obj = registry.get('sale.order.line')
        users_obj = registry.get('res.users')
        promotion_user = registry.get('qdodoo.user.promotion')
        product_price_dict = self.get_minus_money(cr, uid, order, promotion_obj, promotion_user, users_obj)
        minus_money = 0
        for key,valus in product_price_dict.items():
            minus_money += valus
        sale_order_obj = registry.get('sale.order')
        sale_order_obj.write(cr, uid, order.id, {'minus_money':minus_money})
        return request.redirect("/shop/payment")

    # 获取满赠产品数量
    def get_minus_gift(self, cr, uid, order, promotion_obj, promotion_user, users_obj):
        # 获取对应的{产品:数量}
        num_dict = {}
        for line in order.order_line:
            if line.product_id.id in num_dict:
                num_dict[line.product_id.id] += line.multiple_number
            else:
                num_dict[line.product_id.id] = line.multiple_number
        # 判断是否有对应的满赠促销单
        date = datetime.datetime.now().date().strftime('%Y-%m-%d')
        version = ''
        promotion_id = promotion_obj.search(cr, uid, [('selection_ids','=','gift'),('company_id','=',users_obj.browse(cr, uid, uid).company_id.id)])
        if promotion_id:
            promotion_user_ids = promotion_user.search(cr, uid, [('user','=',uid),('promotion','=',promotion_id[0])])
            if not promotion_user_ids:
                return {}
            # 判断是否有满足时间条件的版本
            for line in promotion_obj.browse(cr, uid, promotion_id[0]).version_gift_id:
                if (line.date_start <= date or not line.date_start) and (line.date_end >= date or not line.date_end):
                    version = line
        # 获取当前登录人的销售团队
        user_section_id = users_obj.browse(cr, uid, uid).default_section_id
        if not user_section_id:
            raise except_orm(_('Warning!'),_('当前登录人未设置销售团队！'))
        # 如果存在满足时间段的版本
        product_num_dict = {}
        if version:
            # 判断满足条件的条目
            for line_key in version.items_id:
                # 如果满足品牌
                if line_key.section_id.id == user_section_id.id or not line_key.section_id:
                    product_num_dict[line_key.product_items] = (line_key.id,line_key.product_items_num,line_key.subtract_money * int(num_dict.get(line_key.product_id.id,0.0) / line_key.all_money))
        return product_num_dict

    # 获取满减金额
    def get_minus_money(self, cr, uid, order, promotion_obj, promotion_user, users_obj):
        # 获取{产品：金额} 更新明细中产品的数量
        # 获取{产品分类：金额}
        num_dict = {}
        cage_dict = {}
        all_money = 0
        for line in order.order_line:
            if line.product_id.categ_id.id in cage_dict:
                cage_dict[line.product_id.categ_id.id] += line.multiple_number * line.price_unit
            else:
                cage_dict[line.product_id.categ_id.id] = line.multiple_number * line.price_unit
            num_dict[line.product_id.id] = line.multiple_number * line.price_unit
            # 获取总金额
            all_money += line.multiple_number * line.price_unit
        # 判断是否有对应的满减促销单
        date = datetime.datetime.now().date().strftime('%Y-%m-%d')
        version = ''
        promotion_id = promotion_obj.search(cr, uid, [('selection_ids','=','reduction'),('company_id','=',users_obj.browse(cr, uid, uid).company_id.id)])
        if promotion_id:
            promotion_user_ids = promotion_user.search(cr, uid, [('user','=',uid),('promotion','=',promotion_id[0])])
            if not promotion_user_ids:
                return {}
            # 判断是否有满足时间条件的版本
            for line in promotion_obj.browse(cr, uid, promotion_id[0]).version_id:
                if (line.date_start <= date or not line.date_start) and (line.date_end >= date or not line.date_end):
                    version = line
        # 如果存在满足时间段的版本
        # 获取当前登录人的销售团队
        user_section_id = users_obj.browse(cr, uid, uid).default_section_id
        if not user_section_id:
            raise except_orm(_('Warning!'),_('当前登录人未设置销售团队！'))
        product_price_dict = {}
        if version:
            # 判断满足条件的条目
            for line_key in version.items_id:
                # 如果满足品牌
                if line_key.section_id.id == user_section_id.id or not line_key.section_id:
                    # 如果有单品
                    if line_key.product_id:
                        if line_key.subtract_money and num_dict.get(line_key.product_id.id,0.0) >= line_key.all_money:
                            if line_key.product_items in product_price_dict:
                                product_price_dict[line_key.product_items] += line_key.subtract_money * int(num_dict.get(line_key.product_id.id,0.0) / line_key.all_money)
                            else:
                                product_price_dict[line_key.product_items] = line_key.subtract_money * int(num_dict.get(line_key.product_id.id,0.0) / line_key.all_money)
                    else:
                        # 如果有分类
                        if line_key.category_id:
                            if line_key.subtract_money and cage_dict.get(line_key.category_id.id,0.0) >=line_key.all_money:
                                if line_key.product_items in product_price_dict:
                                    product_price_dict[line_key.product_items] += line_key.subtract_money * int(cage_dict.get(line_key.category_id.id,0.0) / line_key.all_money)
                                else:
                                    product_price_dict[line_key.product_items] = line_key.subtract_money * int(cage_dict.get(line_key.category_id.id,0.0) / line_key.all_money)
                        else:
                            # 判断总金额
                            if all_money >= line_key.all_money and line_key.subtract_money:
                                if line_key.product_items in product_price_dict:
                                    product_price_dict[line_key.product_items] += line_key.subtract_money * int(all_money / line_key.all_money)
                                else:
                                    product_price_dict[line_key.product_items] = line_key.subtract_money * int(all_money / line_key.all_money)

        return product_price_dict
    # 貌似是最终付款
    @http.route('/shop/payment/validate', type='http', auth="public", website=True)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :
         - UDPATE ME
        """
        # 得到常用的几个字段和值
        cr, uid, context = request.cr, request.uid, request.context
        # 初始化email
        email_act = None
        # 得到销售对象
        sale_order_obj = request.registry['sale.order']
        gift_obj = request.registry['qdodoo.promotion.version.gift.items']
        line_obj = request.registry['sale.order.line']
        promotion_obj = request.registry['qdodoo.promotion']
        users_obj = request.registry['res.users']
        # 发票对象
        invoice_obj = request.registry['account.invoice']
        # 出库单
        picking_obj = request.registry['stock.picking']

        # 如果没有销售订单
        if sale_order_id is None:
            # 调用方法得到销售订单
            order = request.website.sale_get_order(context=context)
        else:
            # 查询出相应的销售订单
            order = request.registry['sale.order'].browse(cr, uid, sale_order_id, context=context)
            # 还是在判断下 当前订单号 和缓存中的是否一致
            assert order.id == request.session.get('sale_last_order_id')
        if not order or not order.amount_total:
            return request.redirect('/shop')
        if not order.partner_id.analytic_account_id:
            raise except_orm(_('Warning!'),_('客户没有设置对应的辅助核算项，请检查客户资料是否正确！'))
        promotion_obj = request.registry['qdodoo.promotion']
        line_obj = request.registry['sale.order.line']
        users_obj = request.registry['res.users']
        promotion_user = request.registry['qdodoo.user.promotion']
        # 获取满减金额
        product_price_dict = self.get_minus_money(cr, uid, order, promotion_obj, promotion_user, users_obj)
        # 获取满赠数量
        product_num_dict = self.get_minus_gift(cr, uid, order, promotion_obj, promotion_user, users_obj)
        minus_money = 0
        for line in order.order_line:
            line_obj.write(cr, uid, line.id, {'product_uom_qty':line.multiple_number})
        for key,valus in product_price_dict.items():
            if valus > 0:
                val = {}
                val['order_id'] = order.id
                val['product_id'] = key.id
                val['product_uom_qty'] = 1.0
                val['product_uom'] = key.uom_id.id
                val['price_unit'] = -valus
                val['name'] = key.name
                line_obj.create(cr ,uid, val)
                minus_money += valus
        for key,valus in product_num_dict.items():
            if valus[1] > 0 and valus[2] > 0:
                val = {}
                val['order_id'] = order.id
                val['product_id'] = key.id
                if valus[1] < valus[2]:
                    val['product_uom_qty'] = valus[1]
                else:
                    val['product_uom_qty'] = valus[2]
                val['product_uom'] = key.uom_id.id
                val['price_unit'] = 0
                val['name'] = key.name
                line_obj.create(cr ,uid, val)
                gift_obj.write(cr, uid, valus[0], {'product_items_num':gift_obj.browse(cr, uid, valus[0]).product_items_num - val['product_uom_qty']})
        user_id = order.partner_id.user_id.id or uid
        section_obj = users_obj.browse(cr, uid, user_id)
        section_obj = users_obj.browse(cr, uid, user_id)
        section_id = section_obj.default_section_id.id if section_obj.default_section_id else False
        if section_id:
            sale_order_obj.write(cr, uid, order.id, {'minus_money':minus_money,'section_id':section_id,'order_policy': 'manual','project_id':order.partner_id.analytic_account_id.id,'user_id':user_id})
        else:
            sale_order_obj.write(cr, uid, order.id, {'minus_money':minus_money,'order_policy': 'manual','project_id':order.partner_id.analytic_account_id.id,'user_id':user_id})
        order.action_button_confirm()
        # send by email
        # 邮件act为销售订单 生成报价单
        email_act = sale_order_obj.action_quotation_send(cr, uid, [order.id], context=request.context)
        sale_order_obj.manual_invoice(cr, uid, [order.id],context=context)
        # 获取对应发票列表id
        inv_ids = []
        inv_ids += [invoice.id for invoice in order.invoice_ids]
        for line in invoice_obj.browse(cr, uid, inv_ids):
            if line.state == 'draft':
                invoice_obj.signal_workflow(cr, uid, [line.id], 'invoice_open')
        # 获取对应的出库单列表id
        pick_ids = []
        pick_ids += [picking.id for picking in order.picking_ids]
        for line in picking_obj.browse(cr, uid, pick_ids):
            if line.state == 'confirmed':
                picking_obj.action_assign(cr, uid, [line.id])
        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset(context=context)

        return request.redirect('/shop/confirmation')

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        cr, uid, context = request.cr, request.uid, request.context

        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.registry['sale.order'].browse(cr, uid, sale_order_id, context=context)
        else:
            return request.redirect('/shop')

        return request.website.render("website_sale.confirmation", {'order': order})

    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):

        """ Payment step. This page proposes several payment means based on available
        payment.acquirer. State at this point :

         - a draft sale order with lines; otherwise, clean context / session and
           back to the shop
         - no transaction in context / session, or only a draft one, if the customer
           did go to a payment.acquirer website but closed the tab without
           paying / canceling
        """

        # 得到常用的环境变量
        cr, uid, context = request.cr, request.uid, request.context
        # 得到相关对象
        pool = request.registry
        payment_obj = request.registry.get('payment.acquirer')
        sale_order_obj = request.registry.get('sale.order')

        # 得到当前销售订单
        order = request.website.sale_get_order(context=context)

        # 判断是否需要重定向
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
        multiple=request.session.get('taylor_session')
        # 客户id
        shipping_partner_id = False
        # 如果存在订单
        if order:
            # 如果有订单的
            if order.partner_shipping_id.id:
                shipping_partner_id = order.partner_shipping_id.id
            else:
                shipping_partner_id = order.partner_invoice_id.id

        values = {
            'order': request.registry['sale.order'].browse(cr, uid, order.id, context=context)
        }
        values['multiple'] = multiple
        values['errors'] = sale_order_obj._get_errors(cr, uid, order, context=context)
        values.update(sale_order_obj._get_website_data(cr, uid, order, context))



        # 得到我想要的账号余额
        partner = pool.get('res.users').browse(cr, uid, uid).partner_id
        have_money = pool.get('res.partner').browse(cr, uid, partner.id).credit
        if have_money >= 0:
            values['credit'] = 0
        else:
            values['credit'] = abs(have_money)
        if not values['errors']:
            acquirer_ids = payment_obj.search(cr, uid, [('website_published', '=', True),
                                                                 ('company_id', '=', order.company_id.id)],
                                              context=context)
            values['acquirers'] = list(payment_obj.browse(cr, uid, acquirer_ids, context=context))
            render_ctx = dict(context, submit_class='btn btn-primary', submit_txt=_('Pay Now'))
            for acquirer in values['acquirers']:
                acquirer.button = payment_obj.render(
                    cr, uid, acquirer.id,
                    order.name,
                    order.amount_total,
                    order.pricelist_id.currency_id.id,
                    partner_id=shipping_partner_id,
                    tx_values={
                        'return_url': '/shop/payment/validate',
                    },
                    context=render_ctx)
        return request.website.render("website_sale.payment", values)

    @http.route(['/shop/user/info'], type='http', auth="public", website=True)
    def user_info_promotion(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
        if uid == 3:
            return request.redirect("/web/login")
        values = {}
        # 获取所有的活动
        promotion_obj = request.registry.get('qdodoo.promotion')
        promotion_ids = promotion_obj.search(cr, uid, [('is_play','=',True)])
        # 获取当前登录人已参加的活动
        promotion_use_obj = request.registry.get('qdodoo.user.promotion')
        promotion_use_ids = promotion_use_obj.search(cr, uid, [('user','=',uid),('promotion','in',promotion_ids)])
        values['promotion_users'] = promotion_use_obj.browse(cr, uid, promotion_use_ids)
        promotion_ids_old = []
        for line in values['promotion_users']:
            promotion_ids_old.append(line.promotion.id)
        # 获取未报名的活动
        promotion_ids_new = list(set(promotion_ids) - set(promotion_ids_old))
        values['promotion'] = promotion_obj.browse(cr, uid, promotion_ids_new)
        return request.website.render("qdodoo_websale_update.promotion",values)

    # 跳转到对账单页面
    @http.route(['/shop/account'], type='http', auth="public", website=True)
    def return_account(self, **post):
        cr, uid, context = request.cr, request.uid, request.context

        url_base = request.registry['ir.config_parameter'].get_param(cr, SUPERUSER_ID, 'web.base.url')
        action_id = request.registry['ir.model.data'].get_object_reference(cr, uid, 'qdodoo_websale_update',
                                                                           'action_account_order')[1]
        url = url_base + '/web#' + 'page=0&limit=80&view_type=list&model=account.move.line' + '&action=%s' % action_id
        ret = "<html><head><meta http-equiv='refresh' content='0;URL=%s'></head></html>" % url
        return ret

    # 0获取优惠失败，请联系管理员；1该优惠您已经报名；2报名成功
    @http.route(['/shop/user/info/data_new'], type='http', auth="public", website=True)
    def data_new(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
        promotion_obj = request.registry.get('qdodoo.user.promotion')
        if not post.get('promotion_id'):
            return '0'
        promotion_ids = promotion_obj.search(cr, uid, [('user','=',uid),('promotion','=',int(post.get('promotion_id')))])
        if promotion_ids:
            return '1'
        else:
            promotion_obj.create(cr, SUPERUSER_ID, {'user':uid,'promotion':int(post.get('promotion_id'))})
            return '2'
