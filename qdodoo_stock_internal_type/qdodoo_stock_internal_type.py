# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api, _
from openerp.osv import osv
import base64,xlrd
import logging

_logger = logging.getLogger(__name__)

class qdodoo_stock_internal_type(models.Model):
    """
        仓库转移增加批量导入功能
    """

    _inherit = 'stock.picking'

    source_location = fields.Many2one('stock.location',u'源库位')
    dest_location = fields.Many2one('stock.location',u'目的库位')
    import_file = fields.Binary(string="导入的模板")

    # 明细导入
    @api.one
    def import_data(self):
        if not self.source_location or not self.dest_location:
            raise osv.except_osv(_(u'提示'), _(u'请先选择源库位和目的库位'))
        if self.import_file:
            try:
                excel = xlrd.open_workbook(file_contents=base64.decodestring(self.import_file))
            except:
                raise osv.except_osv(_(u'提示'), _(u'请使用xls文件进行上传'))
            product_info = excel.sheet_by_index(0)
            product_obj = self.env['product.product']
            move_obj = self.env['stock.move']
            for obj in range(1, product_info.nrows):
                val = {}
                # 获取产品编号产品
                default_code = product_info.cell(obj, 0).value
                if default_code:
                    product_ids = product_obj.search([('default_code','=',default_code),('company_id','=',self.company_id.id)])
                    if not product_ids:
                        raise osv.except_osv(_(u'提示'), _(u'该公司没有编号为%s的产品')%default_code)
                    else:
                        if len(product_ids) > 1:
                            raise osv.except_osv(_(u'提示'), _(u'系统中存在多个产品编号为%s的产品')%default_code)
                        else:
                            val['product_id'] = product_ids[0].id
                            val['name'] = product_ids[0].name
                            val['product_uom'] = product_ids[0].uom_id.id
                else:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品编号不能为空')%obj)
                # 获取数量
                product_uom_qty = product_info.cell(obj, 2).value
                if not product_uom_qty:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品数量不能为空')%obj)
                else:
                    val['product_uom_qty'] = float(product_uom_qty)
                val['location_id'] = self.source_location.id
                val['location_dest_id'] = self.dest_location.id
                val['picking_id'] = self.id
                move_obj.create(val)
            self.write({'import_file': ''})
        else:
            raise osv.except_osv(_(u'提示'), _(u'请先上传模板'))

