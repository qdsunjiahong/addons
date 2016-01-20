# -*- coding: utf-8 -*-

from openerp import models, fields, _, api
from openerp.exceptions import except_orm
import time

class taylor_price_version_list(models.Model):
    """
        添加价格表版本与价格表关联
    """
    _name = "price.list.version"

    pricelist = fields.Many2one('product.pricelist', '价格表', required=True)
    perice_version = fields.Many2one('product.pricelist.version', '价格表版本')

    def _check_date(self, cursor, user, ids, context=None):
        return True

class taylor_pricce_version(models.Model):
    """
        添加一个价格表版本与价格表关联字段
    """

    _inherit = "product.pricelist.version"

    price_list_ref = fields.One2many('price.list.version', 'perice_version', '相关价格表')

    def _check_date(self, cursor, user, ids, context=None):
        return True

class taylor_pricce_list(models.Model):

    _inherit = "product.pricelist.item"

    multipl= fields.Float('倍数')
    price_version_item_id = fields.Many2one('pricelist.prolate.relation',string='关联产品中的价格版本信息')

    _defaults = {
        'multipl':1,
    }

    # 选择产品可以自动关联上产品模板
    def product_id_change(self, cr, uid, ids, product_id, context=None):
        if not product_id:
            return {}
        prod = self.pool.get('product.product').browse(cr, uid, product_id)
        val = {}
        if prod.product_tmpl_id:
            val['product_tmpl_id'] = prod.product_tmpl_id.id
        if prod.code:
            val['name'] = prod.code
        return {'value':val}

    # 倍数限制
    @api.constrains('multipl')
    def _check_quantity_price(self):
        if self.multipl<0:
            raise except_orm(_('Warning!'),_('警告,倍数必须大于0！'))

    # 创建价格表关联到产品中对应数据
    def create(self, cr, uid, vals, context=None):
        res_id = super(taylor_pricce_list, self).create(cr, uid, vals, context=context)
        obj = self.browse(cr, uid, res_id)
        relation_id = self.pool.get('pricelist.prolate.relation')
        # 如果选择了产品模板
        if vals.get('product_tmpl_id'):
            # 在产品中创建对应数据
            res = relation_id.create(cr, uid, {'proce_version':obj.price_version_id.id,'proportion':obj.price_discount,
                                         'fixed':obj.price_surcharge,'multipl':obj.multipl,'ref_product_template':vals.get('product_tmpl_id')}, context=context)
            self.write(cr, uid, res_id, {'price_version_item_id':res})
        return res_id

    # 修改明细修改关联到产品中对应数据
    def write(self, cr, uid, ids, value, context=None):
        super(taylor_pricce_list, self).write(cr, uid, ids, value, context=context)
        if not value.get('price_version_item_id'):
            relation_obj = self.pool.get('pricelist.prolate.relation')
            for obj in self.browse(cr, uid, ids):
                relation_obj.write(cr, uid, obj.price_version_item_id.id, {'proportion':obj.price_discount,'fixed':obj.price_surcharge,'multipl':obj.multipl})
        return True

    def unlink(self, cr, uid, ids, context={}):
        relation_obj = self.pool.get('pricelist.prolate.relation')
        if not context.get('version'):
            for obj in self.browse(cr, uid, ids):
                relation_obj.unlink(cr, uid, obj.price_version_item_id.id,context={'item':True})
        return super(taylor_pricce_list, self).unlink(cr, uid, ids, context=context)

class qdodoo_product_pricelist_inherit(models.Model):
    _inherit = 'product.pricelist'

    partner_all = fields.One2many('product.pricelist.partner','qdodoo_partner_id','业务伙伴')

    def _price_rule_get_multi(self, cr, uid, pricelist, products_by_qty_by_partner, context=None):
        context = context or {}
        date = context.get('date') or time.strftime('%Y-%m-%d')

        products = map(lambda x: x[0], products_by_qty_by_partner)
        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.template')
        product_uom_obj = self.pool.get('product.uom')
        price_type_obj = self.pool.get('product.price.type')

        if not products:
            return {}

        version = False
        lst = {}
        for v in pricelist.version_id:
            if (v.date_start is False) or (v.date_start <= date):
                lst[v] = v.date_end
        # 获取价格表版本
        a = ''
        for line_key,line_value in lst.items():
            if line_key.date_end >= date:
                if not version:
                    a = line_value
                    version = line_key
                else:
                    if a > line_value or not a:
                        version = line_key
            if (line_key.date_end is False) and not version:
                a = line_value
                version = line_key
        if not version:
            raise except_orm(_('Warning!'), _("At least one pricelist has no active version !\nPlease create or activate one."))
        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = categ_ids.keys()

        # 获取对应产品id
        is_product_template = products[0]._name == "product.template"
        prod_ids = []
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            for tmpl in products:
                for product in tmpl.product_variant_ids:
                    prod_ids.append(product.id)
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]
        # 查询对应的价格表明细id
        # Load all rules
        cr.execute(
            'SELECT i.id '
            'FROM product_pricelist_item AS i '
            'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = any(%s)) '
                'AND (product_id IS NULL OR (product_id = any(%s))) '
                'AND ((categ_id IS NULL) OR (categ_id = any(%s))) '
                'AND (price_version_id = %s) '
            'ORDER BY sequence, min_quantity desc',
            (prod_tmpl_ids, prod_ids, categ_ids, version.id))
        item_ids = [x[0] for x in cr.fetchall()]
        items = self.pool.get('product.pricelist.item').browse(cr, uid, item_ids, context=context)

        price_types = {}

        results = {}
        for product, qty, partner in products_by_qty_by_partner:
            results[product.id] = 0.0
            rule_id = False
            price = False

            # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
            # An intermediary unit price may be computed according to a different UoM, in
            # which case the price_uom_id contains that UoM.
            # The final price will be converted to match `qty_uom_id`.
            qty_uom_id = context.get('uom') or product.uom_id.id
            price_uom_id = product.uom_id.id
            qty_in_product_uom = qty
            if qty_uom_id != product.uom_id.id:
                try:
                    qty_in_product_uom = product_uom_obj._compute_qty(
                        cr, uid, context['uom'], qty, product.uom_id.id or product.uos_id.id)
                except except_orm:
                    # Ignored - incompatible UoM in context, use default product UoM
                    pass
            for rule in items:
                # 根据最小数量判断是否匹配
                if rule.min_quantity and qty_in_product_uom < rule.min_quantity:
                    continue
                # 如果是产品模板
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    # 如果明细中存在产品
                    # if rule.product_id:
                    #     continue
                else:
                    if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and product.id != rule.product_id.id:
                        continue
                # 如果产品中有分类
                if rule.categ_id:
                    cat = product.categ_id
                    while cat:
                        if cat.id == rule.categ_id.id:
                            break
                        cat = cat.parent_id
                    if not cat:
                        continue
                if rule.base == -1:
                    if rule.base_pricelist_id:
                        price_tmp = self._price_get_multi(cr, uid,
                                rule.base_pricelist_id, [(product,
                                qty, False)], context=context)[product.id]
                        ptype_src = rule.base_pricelist_id.currency_id.id
                        price_uom_id = qty_uom_id
                        price = currency_obj.compute(cr, uid,
                                ptype_src, pricelist.currency_id.id,
                                price_tmp, round=False,
                                context=context)
                elif rule.base == -2:
                    seller = False
                    for seller_id in product.seller_ids:
                        if (not partner) or (seller_id.name.id != partner):
                            continue
                        seller = seller_id
                    if not seller and product.seller_ids:
                        seller = product.seller_ids[0]
                    if seller:
                        qty_in_seller_uom = qty
                        seller_uom = seller.product_uom.id
                        if qty_uom_id != seller_uom:
                            qty_in_seller_uom = product_uom_obj._compute_qty(cr, uid, qty_uom_id, qty, to_uom_id=seller_uom)
                        price_uom_id = seller_uom
                        for line in seller.pricelist_ids:
                            if line.min_quantity <= qty_in_seller_uom:
                                price = line.price

                else:
                    if rule.base not in price_types:
                        price_types[rule.base] = price_type_obj.browse(cr, uid, int(rule.base))
                    price_type = price_types[rule.base]

                    # price_get returns the price in the context UoM, i.e. qty_uom_id
                    price_uom_id = qty_uom_id
                    price = currency_obj.compute(
                            cr, uid,
                            price_type.currency_id.id, pricelist.currency_id.id,
                            product_obj._price_get(cr, uid, [product], price_type.field, context=context)[product.id],
                            round=False, context=context)
                if price is not False:
                    price_limit = price
                    price = price * (1.0+(rule.price_discount or 0.0))
                    if rule.price_round:
                        price = tools.float_round(price, precision_rounding=rule.price_round)

                    convert_to_price_uom = (lambda price: product_uom_obj._compute_price(
                                                cr, uid, product.uom_id.id,
                                                price, price_uom_id))
                    if rule.price_surcharge:
                        price_surcharge = convert_to_price_uom(rule.price_surcharge)
                        price += price_surcharge

                    if rule.price_min_margin:
                        price_min_margin = convert_to_price_uom(rule.price_min_margin)
                        price = max(price, price_limit + price_min_margin)

                    if rule.price_max_margin:
                        price_max_margin = convert_to_price_uom(rule.price_max_margin)
                        price = min(price, price_limit + price_max_margin)

                    rule_id = rule.id
                break
            # Final price conversion to target UoM
            price = product_uom_obj._compute_price(cr, uid, price_uom_id, price, qty_uom_id)
            results[product.id] = (price, rule_id)
        return results

class qdodoo_pricelist_partner_inherit(models.Model):
    _name = 'product.pricelist.partner'

    qdodoo_partner_id = fields.Many2one('product.pricelist',u'价格表')
    name = fields.Many2one('res.partner',u'业务伙伴',domain=[('customer','=',True)])

    # 创建数据，修改原有的合作伙伴的销售价格表
    def create(self, cr, uid, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        if vals.get('name'):
            # 先修改业务伙伴的销售价格表
            partner_obj.write(cr, uid, vals.get('name'),{'property_product_pricelist':vals.get('qdodoo_partner_id')})
            # 查询其他的关联此业务伙伴的价格表
            obj_ids = self.search(cr, uid, [('name','=',vals.get('name'))])
            if obj_ids:
                super(qdodoo_pricelist_partner_inherit, self).unlink(cr, uid, obj_ids)
        return super(qdodoo_pricelist_partner_inherit, self).create(cr, uid, vals, context=context)

    # 编辑数据，修改原有的合作伙伴的销售价格表
    def write(self, cr, uid, ids, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        obj = self.browse(cr, uid, ids [0])
        if vals.get('name'):
            # 先修改业务伙伴的销售价格表
            partner_obj.write(cr, uid, vals.get('name'),{'property_product_pricelist':obj.qdodoo_partner_id.id})
            # 查询其他的关联此业务伙伴的价格表
            obj_ids = self.search(cr, uid, [('name','=',vals.get('name')),('id','!=',ids[0])])
            if obj_ids:
                super(qdodoo_pricelist_partner_inherit, self).unlink(cr, uid, obj_ids)
            # 修改原有的客户的销售价格表
            partner_obj.write(cr, uid, obj.name.id,{'property_product_pricelist':1})
        return super(qdodoo_pricelist_partner_inherit, self).write(cr, uid, ids, vals, context=context)

    # 删除数据，修改原有的合作伙伴的销售价格表
    def unlink(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        partner_obj = self.pool.get('res.partner')
        if obj.name:
            partner_obj.write(cr, uid, obj.name.id,{'property_product_pricelist':1})
        return super(qdodoo_pricelist_partner_inherit, self).unlink(cr, uid, ids, context=context)