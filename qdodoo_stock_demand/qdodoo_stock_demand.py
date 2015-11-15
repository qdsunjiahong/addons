# -*- coding: utf-8 -*-
###########################################################################################
#
# module name for OpenERP
# Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api
from openerp.osv import osv
import xlrd
import base64
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID
import sys

reload(sys)
sys.setdefaultencoding('utf8')

_logger = logging.getLogger(__name__)

PROCUREMENT_PRIORITIES = [('0', u'不紧急'), ('1', u'一般'), ('2', u'紧急的'), ('3', u'非常紧急')]


class qdodoo_stock_demand(models.Model):
    """
        转换单模型
    """
    _name = 'qdodoo.stock.demand'  # 模型名称
    _description = 'tet.Template.line'  # 模型描述

    name = fields.Char(u'转换单')
    partner_id = fields.Many2one('res.partner', string=u'客户')
    create_datetime = fields.Datetime(string=u'创建日期')
    date_planed = fields.Datetime(string=u'计划日期', required=True)
    location_id = fields.Many2one('stock.warehouse', string=u'仓库',required=True)
    location_id2 = fields.Many2one('stock.location', string=u'需求库位')
    rule_id = fields.Many2one('procurement.rule', 'Rule', track_visibility='onchange')
    origin = fields.Char(u'源单据')
    bom_id = fields.Many2one('mrp.bom', u'物料清单')
    purchase_id = fields.Many2one('purchase.order', u'采购订单')
    priority_new = fields.Selection(PROCUREMENT_PRIORITIES, u'优先级', required=True, select=True, )
    route_ids = fields.Many2many('stock.location.route', 'stock_location_route_demand', 'procurement_id',
                                 'route_id',
                                 'Preferred Routes',required=True)
    group_id = fields.Many2one('procurement.group', string=u'采购组',required=True)
    company_id = fields.Many2one('res.company', string=u'公司')
    state = fields.Selection([('draft', u'草稿'),
                              ('done', u'完成'),
                              ], u'状态')
    qdodoo_stock_product_ids = fields.One2many('qdodoo.stock.product', 'qdodoo_stock_demand_id', u'产品明细')
    import_file = fields.Binary(string="导入的Excel文件")

    _defaults = {
        'create_datetime': datetime.now(),
        'date_planed': datetime.now(),
        'state': 'draft',
        'priority_new': '1',
        'name': lambda obj, cr, uid, context: '/',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid,
                                                                                                 'qdodoo.stock.demand',
                                                                                                 context=c),
    }
    def btn_import_data(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        if wiz.import_file:
            try:
                excel = xlrd.open_workbook(file_contents=base64.decodestring(wiz.import_file))
            except:
                raise osv.except_osv(_(u'提示'), _(u'请使用xls文件进行上传'))
            product_info = excel.sheet_by_index(0)
            product_obj = self.pool.get('product.product')
            company_obj = self.pool.get('res.company')
            qdodoo_obj = self.pool.get('qdodoo.stock.product')
            lst = []
            for obj in range(1, product_info.nrows):
                val = {}
                # 获取产品编号
                default_code = product_info.cell(obj, 0).value
                if not default_code:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品编号不能为空')%obj)
                # 获取产品数量
                product_qty = product_info.cell(obj, 3).value
                if not product_qty:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品数量不能为空')%obj)
                # 获取公司id
                company_name = product_info.cell(obj, 2).value
                if not company_name:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，公司不能为空')%obj)
                company = company_obj.search(cr, uid, [('name','=',company_name)])
                # 查询系统中对应的产品id
                product_id = product_obj.search(cr, uid, [('default_code','=',default_code),('company_id','=',company)])
                if not product_id:
                    raise osv.except_osv(_(u'提示'), _(u'本公司没有编号为%s的产品')%default_code)
                else:
                    product = product_obj.browse(cr, uid, product_id[0])
                    val['product_id'] = product.id
                    val['name'] = product.name
                    val['uom_id'] = product.uom_id.id
                    val['qdodoo_stock_demand_id'] = wiz.id
                    val['product_qty'] = product_qty
                lst.append(val)
            for res in lst:
                qdodoo_obj.create(cr, uid, res)
            self.write(cr, uid, wiz.id, {'import_file':''})
        else:
            raise osv.except_osv(_(u'提示'), _(u'请先上传模板'))

    def change_location_id(self, cr, uid, ids, location_id, context=None):
        if location_id:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, location_id, context=context)
            return {'value': {'location_id2': warehouse.lot_stock_id.id}}
        return {}

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'qdodoo.stock.demand') or '/'
        context = dict(context or {}, mail_create_nolog=True)
        order = super(qdodoo_stock_demand, self).create(cr, uid, vals, context=context)
        return order

    def btn_action_conversion(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        praper_obj = self.pool.get('procurement.order')
        inv_obj = self.browse(cr, uid, ids[0], context=context)
        line_new = self.browse(cr, uid, ids[0], context=context)
        for line in line_new.qdodoo_stock_product_ids:
            values = {
                'stock_demand_number': inv_obj.name,
                'partner_dest_id': inv_obj.partner_id.id,
                'warehouse_id': inv_obj.location_id.id,
                'location_id': inv_obj.location_id2.id,
                'date_planned': inv_obj.date_planed,
                'group_id': inv_obj.group_id.id,
                'origin': inv_obj.origin,
                'priority_new': '1',
                'state': 'confirmed',
                'purchase_id': inv_obj.purchase_id.id,
                'rule_id': inv_obj.rule_id.id,
                'bom_id': inv_obj.bom_id.id,
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'product_uom': line.uom_id.id,
                'qdodoo_stock_demand_id': ids[0],
                'company_id': line_new.company_id.id,
                'order_id_new': line_new.id,
            }
            res = praper_obj.create(cr, uid, values, context=context)
            list_ids = [res]
            if inv_obj.route_ids:
                for i in inv_obj.route_ids:
                    sql = """insert INTO stock_location_route_procurement (procurement_id, route_id) VALUES (%s,%s)""" % (
                        res, i.id)
                    cr.execute(sql)
            a = self.pool.get('procurement.order').run(cr, uid, list_ids, context=context)
        inv_obj.write({'state': 'done'})
        return True

class qdodoo_stock_product(models.Model):
    _name = 'qdodoo.stock.product'

    product_id = fields.Many2one('product.product', string=u'产品', required=True)
    product_qty = fields.Float(string=u'数量', required=True)
    name = fields.Char(u'备注')
    uom_id = fields.Many2one('product.uom', string=u'单位', required=True)
    qdodoo_stock_demand_id = fields.Many2one('qdodoo.stock.demand', string=u'需求单')


    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        res = {}
        res['value'] = {}
        if product_id:
            product_obj = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            res['value']['name'] = product_obj.product_tmpl_id.name
            res['value']['uom_id'] = product_obj.uom_id.id,
            return res
        else:
            return {}
