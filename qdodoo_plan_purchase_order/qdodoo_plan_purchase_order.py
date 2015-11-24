# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
import xlrd,base64
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_plan_purchase_order(models.Model):
    """
        计划转采购单
    """
    _name = 'qdodoo.plan.purchase.order'    # 模型名称
    _description = 'qdodoo.plan.purchase.order'    # 模型描述

    name = fields.Char(u'单号',copy=False)
    location_name = fields.Many2one('stock.warehouse',u'仓库', required=True)
    company_id = fields.Many2one('res.company',u'公司')
    create_date_new = fields.Datetime(u'创建日期')
    minimum_planned_date = fields.Date(u'预计日期')
    location_id = fields.Many2one('stock.location',u'入库库位')
    order_line = fields.One2many('qdodoo.plan.purchase.order.line', 'order_id', u'产品明细',required=True)
    import_file = fields.Binary(string="导入的Excel文件")
    state = fields.Selection([('draft',u'草稿'),('confirmed',u'确认'),('done',u'完成')],u'状态')

    _defaults = {
        'minimum_planned_date': datetime.now().date(),
        'create_date_new': datetime.now(),
        'state': 'draft',
        'company_id': lambda self, cr, uid, ids:self.pool.get('res.users').browse(cr, uid, uid).company_id.id,
    }

    # 导入方法
    def btn_import_data(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        if wiz.import_file:
            try:
                excel = xlrd.open_workbook(file_contents=base64.decodestring(wiz.import_file))
            except:
                raise osv.except_osv(_(u'提示'), _(u'请使用xls文件进行上传'))
            product_info = excel.sheet_by_index(0)
            product_obj = self.pool.get('product.product')
            purchase_line_obj = self.pool.get('qdodoo.plan.purchase.order.line')
            lst = []
            for obj in range(1, product_info.nrows):
                val = {}
                # 获取产品编号
                default_code = product_info.cell(obj, 0).value
                if not default_code:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品编号不能为空')%obj)
                # 获取计划日期
                if product_info.cell(obj, 2).value:
                    plan_date = datetime.strptime(product_info.cell(obj, 2).value, '%Y-%m-%d')
                else:
                    plan_date = datetime.now().date()
                # 获取产品数量
                product_qty = product_info.cell(obj, 3).value
                if not product_qty:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品数量不能为空')%obj)
                # 查询系统中对应的产品id
                product_id = product_obj.search(cr, uid,
                                                [('default_code', '=', default_code), ('company_id', '=', wiz.company_id.id)])
                if not product_id:
                    raise osv.except_osv(_(u'提示'), _(u'%s公司没有编号为%s的产品') % (wiz.company_id.name,default_code))
                product = product_obj.browse(cr, uid, product_id[0])
                val['product_id'] = product.id
                val['price_unit'] = product.standard_price
                val['name'] = product.name
                val['plan_date'] = plan_date
                val['qty'] = product_qty
                val['uom_id'] = product.uom_id.id
                val['order_id'] = wiz.id
                lst.append(val)
            for res in lst:
                purchase_line_obj.create(cr, uid, res)
            self.write(cr, uid, wiz.id, {'import_file': ''})
        else:
            raise osv.except_osv(_(u'提示'), _(u'请先上传模板'))

    # 获取序列号
    def create(self, cr, uid, vals, context=None):
        if not vals.get('name'):
            vals['name'] = self.pool.get('ir.sequence').get( cr, uid, 'qdodoo.plan.purchase.order')
        return super(qdodoo_plan_purchase_order, self).create(cr, uid, vals, context=context)

    # 获取目的库位
    def change_location_id(self, cr, uid, ids, location_id, context=None):
        if location_id:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, location_id, context=context)
            return {'value': {'location_id': warehouse.lot_stock_id.id}}
        return {}

    # 确认
    def btn_draft_confirmed(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('qdodoo.plan.purchase.order.line')
        line_id = line_obj.search(cr, uid, [('order_id','=',ids[0])])
        line_obj.write(cr, uid, line_id, {'state':'done'})
        return self.write(cr, uid, ids, {'state':'confirmed'})

    # 转换采购单
    def btn_confirmed_done(self, cr, uid, ids, context=None):
        purchase_obj = self.pool.get('purchase.order')
        partner_obj = self.pool.get('res.partner')
        purchase_line_obj = self.pool.get('purchase.order.line')
        for obj in self.browse(cr, uid, ids):
            # 循环处理产品明细
            purchase_id = {}
            for line in obj.order_line:
                # 组织采购订单数据
                # 判断是否是同一到货日期和供应商
                if (line.plan_date,line.partner_id.id) in purchase_id:
                    # 如果存在重复的产品
                    all = purchase_id[(line.plan_date,line.partner_id.id)][:]
                    for key in all:
                        if line.product_id.id == key[0]:
                            purchase_id[(line.plan_date,line.partner_id.id)].append((key[0], key[1]+line.qty,key[2],key[3],key[4]))
                            purchase_id[(line.plan_date,line.partner_id.id)].remove(key)
                        else:
                            purchase_id[(line.plan_date,line.partner_id.id)].append((line.product_id.id ,line.qty, line.price_unit,line.name,line.uom_id.id))
                else:
                    purchase_id[(line.plan_date,line.partner_id.id)] = [(line.product_id.id ,line.qty, line.price_unit,line.name,line.uom_id.id)]
            # 创建采购单
            for key_line,value_line in purchase_id.items():
                picking_type_ids = self.pool.get('stock.picking.type').search(cr, uid, [('warehouse_id','=',obj.location_name.id),('default_location_dest_id','=',obj.location_id.id)])
                picking_type_id = picking_type_ids[0] if picking_type_ids else ''
                res_id = purchase_obj.create(cr, uid, {'pricelist_id':partner_obj.browse(cr, uid, key_line[1]).property_product_pricelist_purchase.id,'plan_id':obj.id,'partner_id':key_line[1],'location_name':obj.location_name.id,
                                              'date_order':obj.create_date_new,'company_id':obj.company_id.id,'picking_type_id':picking_type_id,
                                              'location_id':obj.location_id.id,'minimum_planned_date':obj.minimum_planned_date,
                                              })
                # 创建采购订单明细
                for line_va in value_line:
                    purchase_line_obj.create(cr, uid, {'name':line_va[3],'order_id':res_id,'product_id':line_va[0],'date_planned':key_line[0],
                                                       'company_id':obj.company_id.id,'product_qty':line_va[1],'product_uom':line_va[4],
                                                       'price_unit':line_va[2]})
        return self.write(cr, uid, ids, {'state':'done'})

class qdodoo_purchase_order_tfs(models.Model):
    _inherit = 'purchase.order'

    plan_id = fields.Many2one('qdodoo.plan.purchase.order',u'计划单')

class qdodoo_plan_purchase_order_line(models.Model):
    _name = 'qdodoo.plan.purchase.order.line'

    order_id = fields.Many2one('qdodoo.plan.purchase.order',u'计划转采购单')
    product_id = fields.Many2one('product.product',u'产品',required=True)
    plan_date = fields.Date(u'到货日期',required=True)
    name = fields.Char(u'备注')
    price_unit = fields.Float(u'单价')
    qty = fields.Float(u'数量',required=True)
    uom_id = fields.Many2one('product.uom',u'单位')
    partner_id = fields.Many2one('res.partner',u'供应商')
    state = fields.Selection([('draft','draft'),('done','done')],u'状态')

    # 根据产品和供应商修改产品价格
    def onchange_product_id(self, cr, uid, ids, product_id, partner_id, qty, uom_id,context=None):
        product_pricelist = self.pool.get('product.pricelist')
        partner_obj = self.pool.get('res.partner')
        res = {}
        res['value'] = {}
        date_order = datetime.now()
        if product_id:
            product_obj = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            if partner_id:
                pricelist_id = partner_obj.browse(cr, uid, partner_id).property_product_pricelist_purchase.id
                date_order_str = date_order.strftime(DEFAULT_SERVER_DATE_FORMAT)
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                        product_id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
                res['value']['price_unit'] = price
            else:
                res['value']['price_unit'] = product_obj.standard_price
            res['value']['name'] = product_obj.product_tmpl_id.name
            res['value']['uom_id'] = product_obj.uom_id.id
            return res
        else:
            return {}

    _defaults = {
        'state':'draft',
    }


