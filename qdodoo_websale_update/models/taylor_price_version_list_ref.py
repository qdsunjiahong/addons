# -*- coding: utf-8 -*-

from openerp import models, fields, _, api
from openerp.exceptions import except_orm
import time
from datetime import datetime
from openerp import tools
from openerp.osv import osv
import base64,xlrd

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
    import_file = fields.Binary(string="导入的模板")

    @api.model
    def create(self, vals):
        res = super(taylor_pricce_version, self).create(vals)
        self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':res.pricelist_id.name,'note':'创建价格表版本：%s'%res.name})
        return res

    @api.multi
    def write(self, vals):
        if vals.get('active'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.pricelist_id.name,'note':'将价格表版本%s置为无效'%self.name})
        if vals.get('name'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.pricelist_id.name,'note':'将价格表版本的名称由%s改为%s'%(self.name,vals.get('name'))})
        if vals.get('date_start'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.pricelist_id.name,'note':'将价格表版本的开始时间由%s改为%s'%(self.date_start,vals.get('date_start'))})
        if vals.get('date_end'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.pricelist_id.name,'note':'将价格表版本的结束时间由%s改为%s'%(self.date_end,vals.get('date_end'))})
        return super(taylor_pricce_version, self).write(vals)

    # 删除价格表版本
    @api.multi
    def unlink(self):
        self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.pricelist_id.name,'note':'删除价格表版本：%s'%self.name})
        return super(taylor_pricce_version, self).unlink()

    def _check_date(self, cursor, user, ids, context=None):
        return True

    # 明细导入
    @api.one
    def import_data(self):
        if self.import_file:
            try:
                excel = xlrd.open_workbook(file_contents=base64.decodestring(self.import_file))
            except:
                raise osv.except_osv(_(u'提示'), _(u'请使用xls文件进行上传'))
            product_info = excel.sheet_by_index(0)
            pricelist_item_obj = self.env['product.pricelist.item']
            product_obj = self.env['product.product']
            for obj in range(2, product_info.nrows):
                val = {}
                # 获取产品编号产品
                default_code = product_info.cell(obj, 0).value
                if default_code:
                    product_ids = product_obj.search([('default_code','=',default_code)])
                    if len(product_ids) > 1:
                        raise osv.except_osv(_(u'提示'), _(u'系统中存在多个产品编号为%s的产品')%default_code)
                    else:
                        val['product_id'] = product_ids[0].id
                        val['name'] = default_code
                # 获取倍数
                multipl = product_info.cell(obj, 2).value
                if not multipl:
                    val['multipl'] = 1
                else:
                    val['multipl'] = float(multipl)
                # 获取价格计算方法
                base = product_info.cell(obj, 3).value
                if not base:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，价格计算基础不能为空')%obj)
                else:
                    base = int(base)
                    if base not in (1,2):
                        raise osv.except_osv(_(u'提示'), _(u'第%s行，价格计算基础只能填写‘1’或‘2’')%obj)
                    val['base'] = base
                # 获取价格计算比例
                price_discount = product_info.cell(obj, 4).value
                if not price_discount:
                    val['price_discount'] = 0
                else:
                    val['price_discount'] = float(price_discount)
                # 获取价格计算固定值
                price_surcharge = product_info.cell(obj, 5).value
                if not price_surcharge:
                    val['price_surcharge'] = 0
                else:
                    val['price_surcharge'] = float(price_surcharge)
                val['price_version_id'] = self.id
                pricelist_item_obj.create(val)
            self.write({'import_file': ''})
        else:
            raise osv.except_osv(_(u'提示'), _(u'请先上传模板'))

class taylor_pricce_list(models.Model):

    _inherit = "product.pricelist.item"

    multipl= fields.Float('倍数')
    price_version_item_id = fields.Many2one('pricelist.prolate.relation',string='关联产品中的价格版本信息')
    is_recommend = fields.Boolean(u'设置为推荐')

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
        for ids in self:
            if ids.multipl<0:
                raise except_orm(_('Warning!'),_('警告,倍数必须大于0！'))

    @api.model
    # 创建价格表关联到产品中对应数据
    def create(self, vals):
        res_id = super(taylor_pricce_list, self).create(vals)
        self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':res_id.price_version_id.pricelist_id.name,'note':'创建价格表明细：%s'%res_id.name})
        relation_id = self.env['pricelist.prolate.relation']
        # 如果选择了产品模板
        if vals.get('product_tmpl_id'):
            # 在产品中创建对应数据
            res = relation_id.create({'proce_version':res_id.price_version_id.id,'proportion':res_id.price_discount,
                                         'fixed':res_id.price_surcharge,'multipl':res_id.multipl,'ref_product_template':vals.get('product_tmpl_id')})
            res_id.write({'price_version_item_id':res.id})
        return res_id

    @api.multi
    # 修改明细修改关联到产品中对应数据
    def write(self, vals):
        if vals.get('active'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细%s置为无效'%self.name})
        if vals.get('name'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的名称由 %s 改为 %s'%(self.name,vals.get('name'))})
        if vals.get('product_id'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的产品由 %s 改为 %s'%(self.product_id.name if self.product_id else '空',self.sudo().env['product.product'].browse(vals.get('product_id')).name)})
        if vals.get('product_tmpl_id'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的产品模板由 %s 改为 %s'%(self.product_tmpl_id.name if self.product_tmpl_id else '空',self.sudo().env['product.template'].browse(vals.get('product_tmpl_id')).name)})
        if vals.get('categ_id'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的产品分类由 %s 改为 %s'%(self.categ_id.name if self.categ_id else '空',self.sudo().env['product.category'].browse(vals.get('categ_id')).name)})
        if vals.get('multipl'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的倍数由 %s 改为 %s'%(self.multipl,vals.get('multipl'))})
        if vals.get('base'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的价格基础由 %s 改为 %s'%(self.base,vals.get('base'))})
        if vals.get('price_discount'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的新价格比例由 %s 改为 %s'%(self.price_discount,vals.get('price_discount'))})
        if vals.get('price_surcharge'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的新价格固定值由 %s 改为 %s'%(self.price_surcharge,vals.get('price_surcharge'))})
        if vals.get('price_round'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的舍入方法由 %s 改为 %s'%(self.price_round,vals.get('price_round'))})
        if vals.get('price_min_margin'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的最小上浮金额由 %s 改为 %s'%(self.price_min_margin,vals.get('price_min_margin'))})
        if vals.get('price_max_margin'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.price_version_id.pricelist_id.name,'note':'将价格表明细的最大利润由 %s 改为 %s'%(self.price_max_margin,vals.get('price_max_margin'))})
        super(taylor_pricce_list, self).write(vals)
        if not vals.get('price_version_item_id'):
            for obj in self:
                obj.price_version_item_id.write({'proportion':obj.price_discount,'fixed':obj.price_surcharge,'multipl':obj.multipl})
        return True

    def unlink(self, cr, uid, ids, context={}):
        relation_obj = self.pool.get('pricelist.prolate.relation')
        obj_ids = self.browse(cr, uid, ids)
        for line in obj_ids:
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':uid,'pricelist_id':line.price_version_id.pricelist_id.name,'note':'删除价格表明细：%s'%line.name})
        if not context.get('version'):
            for obj in obj_ids:
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
        users_obj = self.pool.get('res.users')
        price_type_obj = self.pool.get('product.price.type')

        if not products:
            return {}

        version = False
        lst = {}
        # 获取开始时间满足条件的价格比明细
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
            # 获取当前登录人用户的价格表
            property_product_pricelist =  users_obj.browse(cr, uid, uid).partner_id.property_product_pricelist
            if property_product_pricelist != pricelist:
                return self._price_rule_get_multi(cr, uid, property_product_pricelist, products_by_qty_by_partner, context=context)
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

    # 创建价格表时插入记录
    @api.model
    def create(self, vals):
        res = super(qdodoo_product_pricelist_inherit, self).create(vals)
        self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':res.name,'note':'创建价格表：%s'%res.name})
        return res

    # 编辑价格表是插入数据
    @api.multi
    def write(self, vals):
        if vals.get('active'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.name,'note':'将价格表%s置为无效'%self.name})
        if vals.get('type'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.name,'note':'将价格表类型由%s修改为%s'%(self.type,vals.get('type'))})
        if vals.get('name'):
            self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.name,'note':'将价格表名称由%s修改为%s'%(self.name,vals.get('name'))})
        return super(qdodoo_product_pricelist_inherit, self).write(vals)

    # 删除价格表
    @api.multi
    def unlink(self):
        self.env['qdodoo.pricelist.edit.line'].create({'name':datetime.now(),'user_id':self._uid,'pricelist_id':self.name,'note':'删除价格表：%s'%self.name})
        return super(qdodoo_product_pricelist_inherit, self).unlink()

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

class qdodoo_pricelist_edit_line(models.Model):
    """
        价格表修改记录
    """
    _name = 'qdodoo.pricelist.edit.line'
    _order = 'id desc'

    name = fields.Datetime(u'修改时间')
    user_id = fields.Many2one('res.users',u'修改人')
    pricelist_id = fields.Char(u'修改的价格表')
    note = fields.Char(u'修改内容')