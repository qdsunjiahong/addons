# -*- coding: utf-8 -*-
################################################################
# 1.必须先把"单位"导入的odoo8.0中  注意分类有个“面积”
# 2.路线必须包括：
#   按照订单生产（make_to_order) Make To Order
#   备货型生产（make_to_stock) 7.0 有，8.0 不需要，则默认是备货型生产
#   生产（produce)  与上面组合  Manufacture
#   购买（buy)                 Buy
#
# 3.先建好父级分类
# ４.提供整体父类，依次会产生子类及产品
#
#
#
################################################################



from openerp.osv import fields, osv
import xmlrpclib

class rain_product_to_v8(osv.osv):
    _name = "rain.product.v8"

    _columns = {
        'name':fields.char('用户名'),
        'password':fields.char('密码'),
        'database':fields.char('数据库'),
        'url':fields.char('数据库地址'),
        'category':fields.char('v7分类'),
    }

    def action_upload(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        # name  = self.browse(cr, uid, ids[0]).name
        # password = self.browse(cr,uid,ids[0]).password
        # database = self.browse(cr,uid,ids[0]).database
        # url = self.browse(cr,uid,ids[0]).url
        # category = self.browse(cr, uid, ids[0]).category

        name  = 'admin'
        password = 'admin'
        database = 'FZ'
        url = 'http://test.wangluodingdan.com:8069'
        category = '全部'

        sock_common = xmlrpclib.ServerProxy(url+"/xmlrpc/common")
        uidl = sock_common.login(database, name ,password)
        sock = xmlrpclib.ServerProxy(url+"/xmlrpc/object")

        iss = sock.execute(database,uidl, password, 'product.category','search',[('name','=',category)])
        categorys = sock.execute(database, uidl, password, 'product.category', 'read',iss)

        current_categ_ids = self.pool.get("product.category").search(cr, uid, [('name','=',category)])
        current_categs = self.pool.get("product.category").browse(cr, uid, current_categ_ids)
        current_c = current_categs[0]
        remote_c = categorys[0]

        self._bulid_child_category(cr, uid, database, uidl, password, sock,current_c.id,remote_c['id'])


    # def _bulid_parent_category(self,cr,uid,database,uidl, password,sock, current_categ_id):
    #     catgs = sock.execute(database, uidl, password, 'product.category', 'read', current_categ_id)
    #     catg = catgs[0]
    #     #检查当前的分类是否存在
    #     product_catge_pool = self.pool.get('product.category')
    #     product_catge_ids = product_catge_pool.search(cr, uid, ['name','=',catg['name']])
    #
    #     #递归调用
    #     if catg['parent_id'] != False:
    #         self._bulid_parent_category(cr,uid,database, uidl, password, sock, catg['parent_id'])
    #     else:
    #         return False


    def _bulid_product_by_remote(self,cr,uid,database, uidl,password, sock, current_categ_id, cate_remote_id):
        """
            根据分类获取远程产品　转换成　当前产品
        :param cr:
        :param uid:
        :param database:
        :param uidl:
        :param password:
        :param sock:
        :param current_categ_id:
        :param current_cate_remote_id:
        :return:
        """
        #print u'创建分类的产品：分类：'
        remote_product_ids = sock.execute(database,uidl, password, 'product.product','search',[('categ_id','=',cate_remote_id)])
        #print remote_product_ids
        if len(remote_product_ids) > 0:
            for remote_product_id in remote_product_ids:
                print remote_product_id
                remote_products = sock.execute(database, uidl, password, 'product.product', 'read',remote_product_id)
                print u'获取到产品'

                #print remote_products
                    #current_product_id = self._covert_remote_to_product(cr,uid,remote_product,current_categ_id)
                    #创建供本地应商
                    # for seller_id in remote_product['seller_ids']:
                    #     self._build_supplier_info_by_remote(cr, uid, database, uidl, password, sock, seller_id, current_product_id)

    def _build_supplier_info_by_remote(self, cr, uid, database, uidl, password, sock,remote_seller_id, current_product_id):
        """
            创建产品供应商信息
        :param cr:
        :param uid:
        :param database:
        :param uidl:
        :param password:
        :param sock:
        :param remote_seller_id: 远程供应商信息id
        :param current_product_id: 当前产品
        :return:
        """
        #获取该产品远程供应商信息
        #iss = sock.execute(database,uidl, password, 'product.supplierinfo','search',[('name','=',category)])
        remote_supplier_info = sock.execute(database, uidl, password, 'product.supplierinfo', 'read',remote_seller_id)
        product_tmpl_id = self.pool.get('product.product').browse(cr, uid, current_product_id).product_tmpl_id.id
        supplier_info_args = {
            'name':None,
            'delay' : remote_supplier_info['delay'],
            'min_qty': remote_supplier_info['min_qty'],
            #'product_id':current_product_id,
            'product_tmpl_id':product_tmpl_id,
        }

        #检查是否存在现有供应商信息
        supplier_name = remote_supplier_info['name'][1]
        supplier_ids = self.pool.get('res.partner').search(cr, uid,[('name','=',supplier_name)])

        if len(supplier_ids) >0:
            #不需要创建
            supplier_info_args['name'] = supplier_ids[0]
        else:
            #创建新的供应商
            remote_supplier_id = remote_supplier_info['name'][0]
            supplier_id = self._build_supplier_by_remote(cr, uid, database, uidl, password, sock, remote_supplier_id)
            supplier_info_args['name'] = supplier_id

        #创建产品供应商信息
        self.pool.get('product.supplierinfo').create(cr, uid, supplier_info_args)

    def _build_supplier_by_remote(self, cr, uid, database, uidl, password, sock, remote_supplier_id):
        """
            创建供应商
        :param cr:
        :param uid:
        :param database:
        :param uidl:
        :param password:
        :param sock:
        :param remote_supplier:
        :return: 供应商 id
        """
        #获取远程供应商信息
        remote_supplier = sock.execute(database, uidl, password, 'res.partner', 'read',remote_supplier_id)


        supplier_args = {
            'name' : remote_supplier['name'],
            'mobile': remote_supplier['mobile'],
            'ref':remote_supplier['ref'],
            'date':remote_supplier['date'],
            'email':remote_supplier['email'],
            'street':remote_supplier['street'],
            'street2':remote_supplier['street2'],
            #'is_internal':remote_supplier['is_internal'],
            'is_company':remote_supplier['is_company'],
            'supplier':remote_supplier['supplier'],
            'comment':remote_supplier['comment']
        }

        #国家 省 市  区 县 街道
        #国家
        if remote_supplier['country_id']:
            country_name = remote_supplier['country_id'][1]
            ids = self.pool.get('res.country').search(cr, uid, [("name", "=", country_name)])
            if len(ids) > 0:
                supplier_args["country_id"] = ids[0]
            else:
                #不存在这个单位
                raise osv.except_osv("国家不存在:", u'国家不存在:'+country_name )

        #
        # #省会
        # state_name = ""
        # if remote_supplier['state_id']:
        #     state_name = remote_supplier['state_id'][1]
        #
        #     ids = self.pool.get('res.country.state').search(cr, uid, [("name", "=", state_name)])
        #     if len(ids) > 0:
        #         supplier_args["state_id"] = ids[0]
        #     else:
        #         #不存在这个单位
        #         raise osv.except_osv(u"省会不存在:", u'省不存在:'+state_name )
        #
        #
        #    #市
        # if remote_supplier['city']:
        #     city_name = remote_supplier['city'][1]
        #
        #     ids = self.pool.get('hm.city').search(cr, uid, [("name", "=", city_name)])
        #     if len(ids) > 0:
        #         supplier_args["city"] = ids[0]
        #     else:
        #         #不存在这个单位
        #         raise osv.except_osv("城市不存在:", u'城市不存在:'+ city_name )
        #
        #    #区
        # if remote_supplier['district']:
        #     district_name = remote_supplier['district'][1]
        #
        #     ids = self.pool.get('hm.district').search(cr, uid, [("name", "=", district_name)])
        #     if len(ids) > 0:
        #         supplier_args["district"] = ids[0]
        #     else:
        #         #不存在这个单位
        #         raise osv.except_osv("区不存在:", u'区不存在:'+district_name+":"+state_name )


        #创建
        return self.pool.get('res.partner').create(cr, uid, supplier_args)



    def _covert_remote_to_product(self,cr ,uid ,remote_product,current_categ_id):
        """
        将　7.0 的产品转换到　8.0 的产品上
        :param cr:
        :param uid:
        :param remote_product:
        :param current_categ_id:
        :return:
        """

        #print remote_product['seller_ids']

        category_obj = self.pool.get("product.category")
        product_obj = self.pool.get("product.product")
        uom_obj = self.pool.get("product.uom")
        location_obj = self.pool.get("stock.location.route")

        args = {}
        args['ean13'] = remote_product['ean13']
        args['incoming_qty'] = remote_product['incoming_qty']
        args['name_template'] = remote_product['name_template']
        args['property_account_income'] = remote_product['property_account_income']
        args['seller_qty'] = remote_product['seller_qty']
        args['message_summary'] = remote_product['message_summary']
        #args['use_time'] = remote_product['use_time']
        args['loc_rack'] = remote_product['loc_rack']
        args['property_stock_account_input'] = remote_product['property_stock_account_input']
        args['sale_delay'] = remote_product['sale_delay']
        args['rental'] = remote_product['rental']
        args['mes_type'] = remote_product['mes_type']
        args['state'] = remote_product['state']
        #args['life_time'] = remote_product['life_time']
        args['price'] = remote_product['price']
        args['seller_delay'] = remote_product['seller_delay']
        args['loc_case'] = remote_product['loc_case']
        args['property_stock_account_output'] = remote_product['property_stock_account_output']
        args['lst_price'] = remote_product['lst_price']
        args['message_unread'] = remote_product['message_unread']
        args['warranty'] = remote_product['warranty']
        args['active'] = remote_product['active']
        args['qty_available'] =remote_product['qty_available']
        args['uos_coeff'] = remote_product['uos_coeff']
        args['track_incoming'] = remote_product['track_incoming']
        args['standard_price'] = remote_product['standard_price']

        args['categ_id'] = current_categ_id
        args['default_code'] = remote_product['code']
        args['name'] = remote_product['name_template']
        args['sale_ok'] = remote_product['sale_ok']
        args['purchase_ok'] = remote_product['purchase_ok']
        args['list_price'] = remote_product['list_price']
        args['type'] = remote_product['type']


        uom_name = remote_product['uom_id'][1]
        #计量单位
        ids = uom_obj.search(cr, uid, [("name", "=", uom_name)])
        if len(ids) > 0:
            args["uom_id"] = ids[0]
            args["uom_po_id"] = ids[0]
        else:
            #不存在这个单位
            raise osv.except_osv("计量单位不存在:", u'计量单位不存在:'+uom_name )

        #供应方法　remote supply_method
        #
        procure_method = remote_product['procure_method']
        supply_method  = remote_product['supply_method']

        route_ids_names = []
        if supply_method == 'buy':
            route_ids_names.append('Buy')
        else:
            route_ids_names.append('Manufacture')
        # 按订单生产
        if procure_method == 'make_to_order':
            route_ids_names.append(['Make To Order'])
            #[remote_product['supply_method'],remote_product['procure_method']]
        r_ids = location_obj.search(cr, uid, [('name', 'in', route_ids_names)])
        args['route_ids'] = [(6, 0, r_ids)]


        #cost_method
        args['cost_method'] = remote_product['cost_method']

        #args['track_production'] = remote_product['track_production']
        args['track_incoming'] = remote_product['track_incoming']

        args['warranty'] = remote_product['warranty']
        args['valuation'] = remote_product['valuation']

        return  product_obj.create(cr, uid, args)

    def _bulid_child_category(self,cr,uid,database,uidl, password, sock, current_categ_id,current_cate_remote_id):
        """
            递归建立远程子分类
        :param cr:
        :param uid:
        :param database:
        :param uidl:
        :param password:
        :param sock:
        :param current_categ_id:
        :param current_cate_remote_id:
        :return:
        """
        #获取远程产品

            #获取远程子类
        catg = sock.execute(database, uidl, password, 'product.category', 'read', current_cate_remote_id)
        #print catg
        child_ids = catg['child_id']
        #创建当前分类产品
        #self._bulid_product_by_remote(cr, uid, database, uidl, password, sock, current_categ_id,current_cate_remote_id)
        #print u'产品创建完成'
        if len(child_ids) == 0:
            return False
        else:
            child_catgs = sock.execute(database, uidl, password, 'product.category', 'read', child_ids)
            for i in range(0, len(child_catgs)):
                category = {
                    'name':child_catgs[i]['name'],
                    'parent_id':current_categ_id
                }
                #child_id = sock.execute(database,uidl, password, 'product.category', 'create', category)
                #创建新的子级
                child_id = self.pool.get('product.category').create(cr,uid,category)
                self._bulid_child_category(cr,uid,database,uidl,password,sock,child_id,child_catgs[i]['id'])

