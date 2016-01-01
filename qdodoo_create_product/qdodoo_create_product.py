# encoding:utf-8

from openerp import models, api, _, fields
from openerp.osv import osv
from openerp.exceptions import except_orm
import xlrd,base64
from datetime import datetime

class qdodoo_product_template(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        res = super(qdodoo_product_template, self).create(vals)
        company_id = vals.get('company_id', False)
        if company_id:
            location_id = self.env['stock.location'].search(
                [('company_id', '=', company_id), ('usage', '=', 'inventory')])
            res.write({'property_stock_inventory': location_id})
        return res

class qdodoo_product_onchange(models.Model):
    _name = 'qdodoo.product.onchange'

    import_file = fields.Binary(u'上传文件')

    def action_search(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        if wiz.import_file:
            try:
                excel = xlrd.open_workbook(file_contents=base64.decodestring(wiz.import_file))
            except:
                raise osv.except_osv(_(u'提示'), _(u'请使用xls文件进行上传'))
            product_info = excel.sheet_by_index(0)
            product_obj = self.pool.get('product.template')
            company_obj = self.pool.get('res.company')
            for obj in range(1, product_info.nrows):
                val = {}
                # 获取原产品编号
                default_code = product_info.cell(obj, 1).value
                if not default_code:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品编号不能为空')%obj)
                # 获取公司id
                company_name = product_info.cell(obj, 4).value
                if not company_name:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，公司不能为空')%obj)
                company = company_obj.search(cr, uid, [('name','=',company_name)])
                if not company:
                    raise osv.except_osv(_(u'提示'), _(u'未在系统中查询到%s公司') % company_name)
                # 查询系统中对应的产品模板id
                product_id = product_obj.search(cr, uid, [('default_code', '=', default_code), ('company_id', '=', company[0])])
                if not product_id:
                    raise osv.except_osv(_(u'提示'), _(u'本公司没有编号为%s的产品') % default_code)
                # 获取新产品编号
                default_code_new = product_info.cell(obj, 2).value
                if not default_code_new:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，新产品编号不能为空')%obj)
                for product in product_id:
                    product_obj.write(cr, uid, product, {'default_code':default_code_new})
        else:
            raise osv.except_osv(_(u'提示'), _(u'请先上传模板'))

class qdodoo_product_type_period(models.Model):
    _name = 'qdodoo.product.type.period'

    import_file = fields.Binary(u'上传文件')

    def action_search(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        if wiz.import_file:
            try:
                excel = xlrd.open_workbook(file_contents=base64.decodestring(wiz.import_file))
            except:
                raise osv.except_osv(_(u'提示'), _(u'请使用xls文件进行上传'))
            product_info = excel.sheet_by_index(0)
            journal_obj = self.pool.get('account.journal')
            category_obj = self.pool.get('product.category')
            company_obj = self.pool.get('res.company')
            category_obj_all = category_obj.browse(cr, uid, category_obj.search(cr, uid, []))
            for obj in range(1, product_info.nrows):
                val = {}
                # 获取分类
                category = product_info.cell(obj, 0).value
                if not category:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品分类不能为空')%obj)
                # 查询系统中对应的分类id
                category_id = ''
                for category_ids in category_obj_all:
                    if category_ids.complete_name == category:
                        category_id = category_ids.id
                        break
                if not category_id:
                    raise osv.except_osv(_(u'提示'), _(u'系统中没有 %s 产品分类')%category)
                # 获取公司id
                company_name = product_info.cell(obj,1).value
                if not company_name:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，公司不能为空')%obj)
                company = company_obj.search(cr, uid, [('name','=',company_name)])
                if not company:
                    raise osv.except_osv(_(u'提示'), _(u'未在系统中查询到%s公司') % company_name)
                # 查询系统中对应的库存账簿
                journal_id = journal_obj.search(cr, uid, [('name', '=', '库存账簿'), ('company_id', '=', company[0])])
                if not journal_id:
                    raise osv.except_osv(_(u'提示'), _(u'%s公司没有库存账簿') % company[0])
                # 更新分类中的库存账簿
                category_obj.write(cr, uid, category_id, {'property_stock_journal':journal_id[0]})
        else:
            raise osv.except_osv(_(u'提示'), _(u'请先上传模板'))
