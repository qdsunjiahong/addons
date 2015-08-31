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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import SUPERUSER_ID


class qdodoo_purchase_import(models.Model):
    """
        采购明细导入
    """
    _inherit = 'purchase.order'    # 继承

    import_file = fields.Binary(string="导入的模板")

    def import_data(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        if wiz.import_file:
            try:
                excel = xlrd.open_workbook(file_contents=base64.decodestring(wiz.import_file))
            except:
                raise osv.except_osv(_(u'提示'), _(u'请使用xls文件进行上传'))
            product_info = excel.sheet_by_index(0)
            product_obj = self.pool.get('product.product')
            company_obj = self.pool.get('res.company')
            purchase_line_obj = self.pool.get('purchase.order.line')
            product_pricelist = self.pool.get('product.pricelist')
            lst = []
            for obj in range(1, product_info.nrows):
                val = {}
                # 获取产品编号
                default_code = product_info.cell(obj, 0).value
                if not default_code:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品编号不能为空')%obj)
                # 获取计划日期
                if product_info.cell(obj, 3).value:
                    plan_date = datetime.strptime(product_info.cell(obj, 3).value, '%Y-%m-%d')
                else:
                    plan_date = datetime.now().date()
                # 获取产品数量
                product_qty = product_info.cell(obj, 4).value
                if not product_qty:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品数量不能为空')%obj)
                # 获取公司id
                company_name = product_info.cell(obj, 2).value
                if not company_name:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，公司不能为空')%obj)
                company = company_obj.search(cr, uid, [('name','=',company_name)])
                if not company:
                    raise osv.except_osv(_(u'提示'), _(u'未在系统中查询到%s公司') % company_name)
                # 查询系统中对应的产品id
                product_id = product_obj.search(cr, uid,
                                                [('default_code', '=', default_code), ('company_id', '=', company[0])])
                if not product_id:
                    raise osv.except_osv(_(u'提示'), _(u'本公司没有编号为%s的产品') % default_code)
                product = product_obj.browse(cr, uid, product_id[0])

                pricelist_id = wiz.pricelist_id.id
                if pricelist_id:
                    date_order_str = datetime.strptime(wiz.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                    price = product_pricelist.price_get(cr, uid, [pricelist_id],
                            product.id, product_qty, wiz.partner_id or False, {'uom': product.uom_id.id, 'date': date_order_str})[pricelist_id]
                else:
                    price = product.standard_price
                val['product_id'] = product.id
                val['name'] = product.name
                val['date_planned'] = plan_date
                val['company_id'] = product.company_id.id
                val['product_qty'] = product_qty
                val['product_uom'] = product.uom_id.id
                val['price_unit'] = product_info.cell(obj, 5).value if product_info.cell(obj, 5).value else price
                val['order_id'] = wiz.id
                lst.append(val)
            for res in lst:
                purchase_line_obj.create(cr, uid, res)
            self.write(cr, uid, wiz.id, {'import_file': ''})
        else:
            raise osv.except_osv(_(u'提示'), _(u'请先上传模板'))

