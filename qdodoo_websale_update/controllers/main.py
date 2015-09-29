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
        product_obj = pool['product.product']
        for key, value in kw.items():
            if int(value) > 0:
                sql = "SELECT id   FROM product_product where product_tmpl_id=%s" % key
                cr.execute(sql)
                product_id = cr.fetchall()[0]
                request.website.sale_get_order(force_create=1)._cart_update(product_id=int(product_id[0]),
                                                                            add_qty=float(value),
                                                                            set_qty=float(set_qty))

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
        print '====================================shop'
        # 得到搜索区间
        domain = request.website.sale_product_domain()
        # 如果存在搜索
        if search:
            # 遍历每个搜索条件
            for srch in search.split(" "):
                # 把搜索条件转化为 oa代码 区间集合
                domain += ['|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                           ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]
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
        print  "context['pricelist']", context['pricelist']
        # 搜索产品价格表中的产品
        pricelist_version_ids = pool.get('product.pricelist.version').search(cr, uid,[('pricelist_id','=',context['pricelist'])],context=context)
        print 'pricelist_version_ids',pricelist_version_ids
        pricelist_procuct_item_ids=pool.get('product.pricelist.item').search(cr,uid,[('price_version_id','in',pricelist_version_ids)],context=context)
        print  'pricelist_procuct_item_ids',pricelist_procuct_item_ids
        pricelist_procuct_ids=[]
        for search_id in pricelist_procuct_item_ids:
            product_item=pool.get('product.pricelist.item').browse(cr,uid,search_id,context=context)[0]
            print 'product_item',product_item
            print 'pricelist_procuct_ids.product_id',product_item.product_id.id
            if product_item.product_id.id:
                cr.execute("SELECT product_tmpl_id   FROM product_product where id=%s" % product_item.product_id.id)
                pricelist_procuct_ids.append(cr.fetchall())
            else:
                cr.execute("SELECT product_tmpl_id   FROM product_product")
                pricelist_procuct_ids=cr.fetchall()
                print 'else pricelist_procuct_ids:',pricelist_procuct_ids
                break
        domain+=[('id','in',pricelist_procuct_ids)]


        # 更改查询数据
        print 'finally if domain  is', domain
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
        print 'uid', uid, 'limit', PPG, 'offset', pager['offset']
        product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'],
                                         order='website_published desc, website_sequence desc', context=context)
        print 'product_ids', product_ids
        # 产品 查询对应的产品书
        products = product_obj.browse(cr, uid, product_ids, context=context)
        print 'products', products
        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)

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
        print "======================shop products", values.get(products)
        return request.website.render("website_sale.products", values)
