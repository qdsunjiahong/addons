# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import xlrd, base64
from openerp.tools.translate import _
import sys
import types

reload(sys)
sys.setdefaultencoding('utf8')


class rain_product_import(osv.osv):
    _name = "rain.product.import"

    _columns = {
        'db_datas': fields.binary('Database Data'),
    }

    def action_upload(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        value = self.browse(cr, uid, ids[0]).db_datas
        wb = xlrd.open_workbook(file_contents=base64.decodestring(value))

        sh = wb.sheet_by_index(0)
        nrows = sh.nrows
        sh_category_id = None

        category_pool = self.pool.get("product.category")
        product_pool = self.pool.get("product.template")

        uom_obj = self.pool.get("product.uom")
        location_obj = self.pool.get("stock.location.route")

        # 获取所有的分类
        category_ids = category_pool.search(cr, uid, [])
        category_objs = category_pool.browse(cr, uid, category_ids)

        last_product_id = None
        last_default_code = None

        # 获取已经存在的 所有 default_code
        product_ids = product_pool.search(cr, uid, [])
        default_codes = product_pool.read(cr, uid, product_ids, ['default_code'])


        # 获取规格对象
        product_attribute_guige_ids = self.pool.get('product.attribute').search(cr, uid, [('name', '=', u'规格')])
        if len(product_attribute_guige_ids) == 0:
            raise osv.except_osv("导入出错:", _(u'没有建立 规格 属性'))
        product_attribute_guige_id = product_attribute_guige_ids[0]
        product_attribute_value_pool = self.pool.get('product.attribute.value')
        product_attribute_line_pool = self.pool.get('product.attribute.line')
        return_list = []
        for rownum in range(2, nrows):
            args = {}

            # 类别 0
            sh_category = sh.cell(rownum, 0).value
            if sh_category != "":
                sh_category = sh_category.strip()
                for category_obj in category_objs:
                    if category_obj.complete_name == sh_category:
                        args['categ_id'] = category_obj.id
                        break
                else:
                    raise osv.except_osv("导入出错:", _(u'产品分类:' + sh_category + u',请在分类中添加该产品分类;行号:%d' % (rownum + 1)))
            else:
                args['categ_id'] = sh_category_id


            # 编码 1 物料编码 可能出现数字形式的

            sh_default_code = sh.cell(rownum, 1).value
            if sh_default_code != "":
                if type(sh_default_code) == type(1) or type(sh_default_code) == type(1.0):

                    # 是数字
                    args['default_code'] = '%d' % int(sh_default_code)
                    sh_default_code = '%d' % int(sh_default_code)
                else:
                    args['default_code'] = sh_default_code

                # 检查是否重复 default_codes
                if sh_default_code in default_codes:
                    raise osv.except_osv("导入出错:", _(u'物料编码:' + sh_default_code + u'重复，请添加该编码;行号:%d' % (rownum + 1)))
            else:
                raise osv.except_osv("导入出错:", _(u'物料编码:' + sh_default_code + u'不存在，请添加该编码;行号:%d' % (rownum + 1)))


            # 物料名称 2
            product_name = sh.cell(rownum, 2).value.strip()
            if product_name != "":
                args['name'] = product_name
            else:
                # 空
                pass

            # 规格 3 product_attribute_line 中 分别 添加 product_tmpl_id attribute_id value_ids
            # 检查 该规格是否存在在这个 先建立产品


            # 可销售 sale_ok 4

            sale_ok = sh.cell(rownum, 4).value.strip()
            if sale_ok != "":
                if sale_ok == "Y":
                    args['sale_ok'] = True
                else:
                    args['sale_ok'] = False
            else:
                # 空
                args['sale_ok'] = False


            # 可被采购 purchase_ok 5
            purchase_ok = sh.cell(rownum, 5).value.strip()
            if purchase_ok != "":
                if purchase_ok == "Y":
                    args['purchase_ok'] = True
                else:
                    args['purchase_ok'] = False
            else:
                # 空
                args['purchase_ok'] = False

            # 标价（销售价格） list_price 6
            list_price = sh.cell(rownum, 6).value
            if list_price != "":
                args['list_price'] = list_price
            else:
                # 空
                pass

            # 产品类型 type[product(库存商品), consu(消耗品), service(服务)] 6
            sh_type = sh.cell(rownum, 7).value.strip()
            if sh_type != "":
                if sh_type == u"库存商品":
                    args['type'] = "product"
                elif sh_type == u"消耗品":
                    args['type'] = "consu"
                elif sh_type == u"服务":
                    args['type'] = "service"
                else:
                    # 不在列表中
                    raise osv.except_osv("导入出错:",
                                         _(u'产品类型不存在:' + sh_type + u';产品类型包括:库存产品,消耗品,服务;行号:%d' % (rownum + 1)))
            else:
                # 空
                pass


            # 计量单位 uom_id 7 uom_po_id:采购单位
            uom_id = sh.cell(rownum, 8).value.strip()
            if uom_id != "":
                ids = uom_obj.search(cr, uid, [("name", "=", uom_id)])
                if len(ids) > 0:
                    args["uom_id"] = ids[0]
                    args["uom_po_id"] = ids[0]
                else:
                    # 不存在这个单位
                    raise osv.except_osv("导入出错:", _(u'计量单位不存在:' + uom_id + u';请添加该产品计量单位;行号:%d' % (rownum + 1)))
                    pass
            else:
                # 空
                pass


            # 供应方法  (many2many) route_ids (8.0 路线)
            # 默认 (name 值  stock.location.route) 生产,购买,按订单生产
            # Excel 表格中 用 "," 分开

            routes = sh.cell(rownum, 9).value.strip()
            routes_array = routes.split(',')
            # 按订单生产
            r_ids = location_obj.search(cr, uid, [('name', 'in', routes_array)])
            args['route_ids'] = [(6, 0, r_ids)]


            # 成本计算方法 cost_method(标准价格 standard,平均价格 average,实时价格 real)
            cost_method = sh.cell(rownum, 10).value.strip()
            if cost_method != "":
                if cost_method == u"标准价格":
                    args['cost_method'] = "standard"
                elif cost_method == u"平均价格":
                    args['cost_method'] = "average"
                elif cost_method == u"实时价格":
                    args['cost_method'] = "real"
                else:
                    # 不在列表中
                    raise osv.except_osv(
                        _("导入出错:", u'成本计算方法错误:' + cost_method + u'(成本计算方法只有:标准价格,平均价格,实时价格);行号:%d' % (rownum + 1)))
                    pass
            else:
                # 空
                pass

            # 成本价 standard_price
            standard_price = sh.cell(rownum, 11).value
            if standard_price != "":
                args['standard_price'] = standard_price
            else:
                # 空
                pass

            # 产品经理 12

            # 追踪生产批次 13 track_production
            track_production = sh.cell(rownum, 13).value.strip()
            if track_production != "":
                if track_production == "Y":
                    args['track_production'] = True
                else:
                    args['track_production'] = False
            else:
                # 空
                args['track_production'] = False



            # 追踪入库批次 14 track_incoming
            track_incoming = sh.cell(rownum, 14).value.strip()
            if track_incoming != "":
                if track_incoming == "Y":
                    args['track_incoming'] = True
                else:
                    args['track_incoming'] = False
            else:
                # 空
                args['track_incoming'] = False


            # 质保（月） 15 warranty
            warranty = sh.cell(rownum, 15).value
            if warranty != "":
                args['warranty'] = warranty
            else:
                # 空
                pass

            # 库存核算 16  valuation ( 定期 : manual_periodic, 实时 real_time)
            valuation = sh.cell(rownum, 16).value.strip()
            if valuation != "":
                if valuation == u"定期":
                    args['valuation'] = "manual_periodic"
                elif valuation == u"实时":
                    args['valuation'] = "real_time"
                else:
                    raise osv.except_osv("导入出错:", _(u'库存核算:' + valuation + u'(库存核算只有:定期,实时);行号:%d' % (rownum + 1)))
                    pass
            else:
                # 空
                pass

            product_tmpl_id = product_pool.create(cr, uid, args, context=context)

            # 供应商 17 supplier_ref
            supplier_info_args = {}
            supplier_ref = None

            sh_supplier_ref = sh.cell(rownum, 17).value
            # if type(sh_supplier_ref) == type(1) or type(sh_supplier_ref) == type(1.0):
            #     #是数字
            #     supplier_ref = ["%d"%int(sh_supplier_ref)]
            if sh_supplier_ref != "":
                supplier_ref = sh_supplier_ref.split(',')
            else:
                pass

            if sh_supplier_ref != "":
                # 最少数量 18 min_qty
                min_qty = sh.cell(rownum, 18).value
                if min_qty == "":
                    min_qty = 0.0


                # 送货周期 19 delay
                delay = sh.cell(rownum, 19).value
                if delay == "":
                    delay = 0

                supplier_info_args['ref'] = supplier_ref
                supplier_info_args['min_qty'] = min_qty
                supplier_info_args['delay'] = delay
                supplier_info_args['product_tmpl_id'] = product_tmpl_id
                self._build_supplier_info(cr, uid, supplier_info_args)

                # 添加规格 3
                guige = sh.cell(rownum, 3).value.strip()
                if guige != "":
                    pro_attr_value_ids = product_attribute_value_pool.search(cr, uid, [('name', '=', guige), (
                        'attribute_id', '=', product_attribute_guige_id)])
                    pro_attr_value_id = None
                    if len(pro_attr_value_ids) == 0:
                        # 创建这个属性值
                        pro_attr_value_id = product_attribute_value_pool.create(cr, uid, {'name': guige,
                                                                                          'attribute_id': product_attribute_guige_id})
                    else:
                        pro_attr_value_id = pro_attr_value_ids[0]
                    line_value = [(6, 0, [pro_attr_value_id])]
                    product_attribute_line_pool.create(cr, uid, {'product_tmpl_id': product_tmpl_id,
                                                                 'attribute_id': product_attribute_guige_id,
                                                                 'value_ids': line_value})
            return_list.append(product_tmpl_id)
        from_model, from_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product',
                                                                                  'product_template_only_form_view')
        tree_model, tree_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product',
                                                                                  'product_template_tree_view')
        return {
            'name': _(u'产品'),
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', return_list)],
            'views': [(tree_id, 'tree'), (from_id, 'form')],
            'view_id': [tree_id],
        }

    def _build_supplier_info(self, cr, uid, supplier_info):
        """
                    supplier_info_args['ref'] = supplier_ref
                    supplier_info_args['min_qty'] = min_qty
                    supplier_info_args['delay'] = delay
                    supplier_info_args['product_tmpl_id']
        :param cr:
        :param uid:
        :param supplier_info:
        :return:
        """
        supplier_list = supplier_info.get('ref', [])
        if supplier_info:
            supplier_ids = self.pool.get("res.partner").search(cr, uid, [('ref', 'in', supplier_list)])
        else:
            raise osv.except_osv("导入出错:", _(u'供应商不存在:' + supplier_info['ref']))

        for supplier_id in supplier_ids:
            supplier_obj = self.pool.get("res.partner").browse(cr, uid, supplier_id)
            su_info = {
                'name': supplier_obj.id,
                'min_qty': supplier_info['min_qty'],
                'delay': supplier_info['delay'],
                'product_tmpl_id': supplier_info['product_tmpl_id']
            }
            self.pool.get('product.supplierinfo').create(cr, uid, su_info)


rain_product_import()
