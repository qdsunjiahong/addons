# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
import datetime
from openerp.exceptions import except_orm
import copy

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
    is_website = fields.Boolean(u'是否是网络报货生成的订单', default=False)

    def create(self, cr, uid, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        if vals.get('partner_id'):
            if not vals.get('project_id'):
                vals['project_id'] = partner_obj.browse(cr, 1, vals.get('partner_id')).analytic_account_id.id
            if not vals.get('warehouse_id'):
                vals['warehouse_id'] = partner_obj.browse(cr, 1, vals.get('partner_id')).out_stock.id
        return super(qdodoo_sale_order_inherit_tfs, self).create(cr, uid, vals, context=context)

    # 计算合计金额
    def _get_all_money(self):
        num = 0.0
        for line in self.order_line:
            num += line.multiple_number * line.price_unit
        self.all_money = num - self.minus_money

class qdodoo_sale_order_return(models.Model):
    """
        销售订单上的反向转移
    """
    _name = 'qdodoo.sale.order.return'

    order_line = fields.One2many('qdodoo.sale.order.return.line','order_id',u'产品明细')
    invoice_state = fields.Selection([('2binvoiced',u'开票'),('none',u'没有发票')],u'开发票',default='2binvoiced')

    # 获取默认明细产品
    @api.model
    def default_get(self, fields_list):
        res = super(qdodoo_sale_order_return, self).default_get(fields_list)
        # 获取销售订单数据
        sale_id = self.env['sale.order'].browse(self._context.get('active_id'))
        order_line = []
        for line in sale_id.order_line:
            order_line.append({'product_id':line.product_id.id,'quantity':line.product_uom_qty})
        res.update({'order_line': order_line})
        return res

    @api.multi
    def get_bom_product(self):
        bom_ids = self.env['mrp.bom'].search([('type','=','phantom')])
        res = {}
        for bom_id in bom_ids:
            res[bom_id.product_tmpl_id] = bom_id
        return res

    @api.multi
    def btn_return(self):
        # 获取销售订单数据
        sale_id = self.env['sale.order'].browse(self._context.get('active_id'))
        move_obj = self.env['stock.move']
        picking_ids = []
        # 获取所有组合品对应的bom
        bom_product = self.get_bom_product()
        # 获取销售订单的所有出库单
        for picking_id in sale_id.picking_ids:
            if picking_id.state == 'done':
                picking_ids.append(picking_id.id)
        if not picking_ids:
            raise except_orm(_(u'警告!'),_(u'销售订单没有有效的出库单！'))
        else:
            product_dict = {} #{产品:数量}
            for line in self.order_line:
                # 如果产品是组合品，则拆分对应的明细
                if line.product_id.product_tmpl_id in bom_product:
                    for bom_line in bom_product[line.product_id.product_tmpl_id].bom_line_ids:
                        if bom_line.product_id in product_dict:
                            product_dict[bom_line.product_id] += line.quantity/bom_product[line.product_id.product_tmpl_id].product_qty*bom_line.product_qty
                        else:
                            product_dict[bom_line.product_id] = line.quantity/bom_product[line.product_id.product_tmpl_id].product_qty*bom_line.product_qty
                else:
                    if line.product_id in product_dict:
                        product_dict[line.product_id] += line.quantity
                    else:
                        product_dict[line.product_id] = line.quantity
        # 创建对应的反向转移数据
        valu = {}
        product_return_moves = []
        for key,value in product_dict.items():
            # 查询产品对应的调拨单
            move_ids = move_obj.search([('state','=','done'),('product_id','=',key.id),('picking_id','in',picking_ids)])
            if move_ids:
                product_return_moves.append((0,0,{'product_id':key.id,'quantity':value,'move_id':move_ids[0].id}))
            else:
                raise except_orm(_(u'警告!'),_(u'产品%s没有关联有效的出库单！')%key.name)
        valu['invoice_state'] = self.invoice_state
        valu['product_return_moves'] = product_return_moves
        ctx = dict(self._context)
        ctx['active_id'] = picking_ids[0]
        ctx['active_ids'] = [picking_ids[0]]
        ctx['active_model'] = 'stock.picking'
        res = self.env['stock.return.picking'].with_context(ctx).create(valu)
        return res.create_returns()

class qdodoo_sale_order_return_line(models.TransientModel):
    """
        销售订单上的反向转移明细
    """
    _name = 'qdodoo.sale.order.return.line'

    order_id = fields.Many2one('qdodoo.sale.order.return',u'反向转移')
    product_id = fields.Many2one('product.product',u'产品')
    quantity = fields.Float(u'数量')


class qdodoo_product_category_inherit(models.Model):
    """
        产品分类增加网络报货倍数
    """
    _inherit = 'product.category'

    fold = fields.Float(u'倍数')

class qdodoo_stock_return_picking_inherit(models.TransientModel):
    """
        修改开发票方式的默认值
    """
    _inherit = 'stock.return.picking'

    # 退货时根据原单据是否有业务伙伴确定退货的开票状态,有业务伙伴则开票。
    @api.model
    def default_get(self, fields):
        res = super(qdodoo_stock_return_picking_inherit, self).default_get(fields)
        record_id = self._context and self._context.get('active_id', False) or False
        picking = self.env['stock.picking'].browse(record_id)
        if picking.partner_id:
            res['invoice_state'] = '2binvoiced'
        return res


