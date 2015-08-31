# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import xlrd,base64

class sale_order(osv.osv):
    '''
        继承sale.order
        增加通过excel 导入sale.order.line 数据
    '''
    _inherit = 'sale.order'

    #columns
    _columns ={
        'data' :fields.binary(string=u'导入的Excel文件')
    }


    def import_data(self, cr, uid, ids, context=None):
        sale_order_objs = self.browse(cr, uid, ids)
        if len(sale_order_objs) > 0:
            sale_order_obj = sale_order_objs[0]
        else:
            raise osv.except_orm(u'销售订单不存在', u'销售订单不存在')

        if sale_order_obj.data :
            excel = xlrd.open_workbook(file_contents=base64.decodestring(sale_order_obj.data))
            #全部采用excel 第一个 sheet
            sheet = excel.sheet_by_index(0)
            for row in range(4,sheet.nrows-5):
                line_args = {
                    'order_id':ids[0]
                }
                #编码 必填
                sh_default_code = sheet.cell(row, 1).value
                if sh_default_code:
                    default_code = None
                    if type(sh_default_code) == type(1) or type(sh_default_code) == type(1.0):
                        #是数字
                        default_code = '%d'%int(sh_default_code)
                    else:
                        #字符串
                        default_code = sh_default_code
                    #获取产品 根据 defaut_code
                    product_product_ids = self.pool.get("product.product").search(cr, uid, [('default_code','=',default_code)])

                    if len(product_product_ids) > 0:
                        product_product_id = product_product_ids[0]
                        product = self.pool.get('product.product').browse(cr, uid, product_product_id)
                        line_args['product_id'] = product.id
                        line_args['product_uom'] = product.uom_id.id
                        line_args['name'] = product.name
                    else:
                        raise osv.except_orm(u'产品不存在（检查编码）',u'错误发生在EXCEl表的第%d行' %(row+1))

                else:
                    raise osv.except_orm(u'编码不能为空！',u'错误发生在EXCEl表的第%d行' %(row+1))

                #数量 必填
                if sheet.cell(row, 5).value:
                    line_args['product_uom_qty'] = sheet.cell(row, 5).value
                else:
                    raise osv.except_orm(u'数量不能为空！',u'错误发生在EXCEl表的第%d行' %(row+1))


                #单价 必填
                if sheet.cell(row, 6).value:
                    line_args['price_unit'] = sheet.cell(row, 6).value
                else:
                    raise osv.except_orm(u'单价不能为空！',u'错误发生在EXCEl表的第%d行' %(row+1))

                #创建 line
                self.pool.get('sale.order.line').create(cr, uid, line_args)

        else:
            raise osv.except_orm(u'没有导入的Excel文件',u'Excle不存在！')