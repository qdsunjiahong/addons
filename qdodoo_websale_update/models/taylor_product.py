# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
import datetime
from openerp.exceptions import except_orm

class taylor_template(models.Model):
    """
        在产品中添加相关价格表关联
        这样可以有效减少业务人员的操作量
    """
    _inherit = 'product.template'

    # 关联字段
    ref_pricelist_prolate = fields.One2many('pricelist.prolate.relation', 'ref_product_template', string='关联的价格表')
    is_gifts = fields.Boolean(u'有赠品')
    gifts_ids = fields.One2many('product.template.gifts','gifts_partner',u'赠品')

    _defaults = {
        'is_gifts':False
    }

class qdodoo_gifts_line(models.Model):
    _name = 'product.template.gifts'

    gifts_partner = fields.Many2one('product.template',u'谁的赠品')
    name = fields.Many2one('product.template',u'赠品')
    number = fields.Float(u'数量')

    _defaults = {
        'number':1.0
    }

class pricelist_prolate_relation(models.Model):
    _name = "pricelist.prolate.relation"

    proce_version=fields.Many2one('product.pricelist.version','价格表版本',required=True)
    proportion = fields.Float('折扣')
    fixed = fields.Float('额外')
    to_toal = fields.Float(string='单价', required=True, compute="compute_toal")
    success = fields.Boolean(string='是否创建', readonly=True)
    comparison = fields.Float(string="对比值", readonly=True)
    multipl=fields.Float(string='倍数')
    company = fields.Many2one('res.company', string='公司')
    price_version_item_id = fields.Many2one('product.pricelist.item',string='对应的价格表版本行')

    # 关联字段
    ref_product_pricelist = fields.Many2one('product.pricelist', '价格表',
                                            domain=['&', ('type', '=', 'sale'), ('company_id', '=', False)])
    ref_product_template = fields.Many2one('product.template', string='产品模版')

    # 获取当前登录人的公司
    def _get_company(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users')
        return user.browse(cr, uid, uid).company_id.id

    _defaults = {
        'company': _get_company,
        'multipl':1,
    }

    # 根据价格表版本，产品模板，查询是否有对应的明细,返回明细lst
    def _get_version_price(self, cr, uid, version_id, product_tmpl_id, context=None):
        version_obj = self.pool.get('product.pricelist.version')
        lst = []
        for line in version_obj.browse(cr, uid, version_id).items_id:
            if line.product_tmpl_id.id == product_tmpl_id:
                lst.append(line.id)
        return lst

    # 倍数必须大于0
    @api.constrains('multipl')
    def _check_quantity_price(self):
        if self.multipl<0:
            raise except_orm(_('Warning!'),_('警告,倍数必须大于0！'))

    # 计算单价
    def compute_toal(self):
        for self_obj in self:
            self_obj.to_toal = (1 + self_obj.proportion) * self_obj.ref_product_template.list_price + self_obj.fixed

    # 根据产品模板获取产品id
    def get_product_tmpl(self, cr, uid, product_tmpl_id, context=None):
        product_obj = self.pool.get('product.product')
        template_ids = product_obj.search(cr, uid, [('product_tmpl_id','=',product_tmpl_id)])
        return template_ids

    # 创建时同步更新对应明细数据
    def create(self, cr, uid, value, context=None):
        re_id = super(pricelist_prolate_relation, self).create(cr, uid, value, context=context)
        version_obj = self.pool.get('product.pricelist.item')
        proce_version = value.get('proce_version')
        ref_product_template = value.get('ref_product_template')
        res_id = self._get_version_price(cr, uid, proce_version, ref_product_template, context=context)
        if res_id:
            version_obj.write(cr, uid, res_id, {'price_discount':value.get('proportion'),'price_surcharge':value.get('fixed'),'multipl':value.get('multipl')})
        else:
            for line in self.get_product_tmpl(cr, uid, ref_product_template, context=context):
                version_obj.create(cr, uid, {'price_discount':value.get('proportion'),'price_surcharge':value.get('fixed'),'multipl':value.get('multipl'),
                                         'price_version_item_id':re_id,'price_version_id':proce_version,'product_id':line,'product_tmpl_id':ref_product_template}, context=context)
        return re_id

    # 修改数据时同步更新对应明细数据
    def write(self, cr, uid, ids, valus, context=None):
        super(pricelist_prolate_relation, self).write(cr, uid, ids, valus, context=context)
        item_obj = self.pool.get('product.pricelist.item')
        for obj in self.browse(cr, uid, ids):
            item_ids = item_obj.search(cr, uid, [('price_version_item_id','=',obj.id)])
            if valus.get('proce_version'):
                # 查询关联的价格表版本信息,删除掉
                item_obj.unlink(cr, uid, item_ids, context={'version':True})
                # 创建新的信息
                for line in self.get_product_tmpl(cr, uid, obj.ref_product_template.id, context=context):
                    item_obj.create(cr, uid, {'price_discount':obj.proportion,'price_surcharge':obj.fixed,'multipl':obj.multipl,
                                         'price_version_item_id':obj.id,'price_version_id':valus.get('proce_version'),'product_id':line,'product_tmpl_id':obj.ref_product_template.id}, context=context)
            else:
                item_obj.write(cr, uid, item_ids, {'price_discount':obj.proportion,'price_surcharge':obj.fixed,'multipl':obj.multipl,'price_version_item_id':obj.id})
        return True

    # 删除同步更新数据
    def unlink(self, cr, uid, ids, context={}):
        item_obj = self.pool.get('product.pricelist.item')
        if not context.get('item'):
        # 查询关联的明细
            for obj in self.browse(cr, uid, ids):
                item_ids = item_obj.search(cr, uid, [('price_version_item_id','=',obj.id)])
                item_obj.unlink(cr, uid, item_ids)
        return super(pricelist_prolate_relation, self).unlink(cr, uid, ids, context=context)

class qdodoo_sale_order_line_inherit_tfs(models.Model):
    _inherit = 'sale.order.line'

    multiple_number = fields.Float(u'数量',help="未乘倍数前的数量")

class qdodoo_sale_order_inherit_tfs(models.Model):
    _inherit = 'sale.order'

    all_money = fields.Float(u'合计',compute='_get_all_money')
    minus_money = fields.Float(u'优惠金额')

    def create(self, cr, uid, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        if vals.get('partner_id'):
            if not vals.get('project_id'):
                vals['project_id'] = partner_obj.browse(cr, 1, vals.get('partner_id')).analytic_account_id.id
            if not vals.get('warehouse_id'):
                vals['warehouse_id'] = partner_obj.browse(cr, 1, vals.get('partner_id')).out_stock.id
        return super(qdodoo_sale_order_inherit_tfs, self).create(cr, uid, vals, context=context)

    def _get_all_money(self):
        num = 0.0
        for line in self.order_line:
            num += line.multiple_number * line.price_unit
        self.all_money = num - self.minus_money

