# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api
from datetime import datetime


class qdodoo_purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    unit_price2 = fields.Float(related='price_unit', string=u'单价')

class qdodoo_product_supplierinfo(models.Model):
    """
        查看产品的供应商价格
    """
    _name = 'qdodoo.product.supplierinfo'

    name = fields.Many2one('product.product',u'产品')
    partner_id = fields.Many2one('res.partner',u'供应商')
    contract_name = fields.Char(u'联系人')
    contract_phone = fields.Char(u'联系电话')
    product_num = fields.Float(u'数量')
    price = fields.Float(u'价格')
    is_true = fields.Boolean(u'有效', default=False)

    # 组织显示数据
    def btn_select(self, cr, uid, ids, context={}):
        cr.execute("""delete from qdodoo_product_supplierinfo""")
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        pricelist_obj = self.pool.get('product.pricelist')
        # 获取所有的产品供应商信息
        product_ids = self.pool.get('product.template').search(cr, uid, [])
        supplierinfo_ids = supplierinfo_obj.search(cr, uid, [('product_tmpl_id','in',product_ids)])
        res_ids = []
        for supplierinfo_id in supplierinfo_obj.browse(cr, uid, supplierinfo_ids):
            # 循环所有的产品
            for product_id in supplierinfo_id.product_tmpl_id.product_variant_ids:
                valus = {}
                valus['name'] = product_id.id
                valus['partner_id'] = supplierinfo_id.name.id
                valus['contract_phone'] = supplierinfo_id.name.phone if supplierinfo_id.name.phone else supplierinfo_id.name.mobile
                if supplierinfo_id.name.child_ids:
                    valus['contract_name'] = supplierinfo_id.name.child_ids[0].name
                # 获取产品模型对应的产品价格
                # 获取供应商的特殊价格
                if supplierinfo_id.pricelist_ids:
                    for pricelist_id in supplierinfo_id.pricelist_ids:
                        valus['product_num'] = pricelist_id.min_quantity
                        valus['price'] = pricelist_id.price
                        if not valus.get('price'):
                            price = 0.0
                        else:
                            price = valus['price']
                        if not valus.get('contract_phone'):
                            contract_phone = False
                        else:
                            contract_phone = valus.get('contract_phone')
                        sql = """
                        insert into qdodoo_product_supplierinfo (name,partner_id,contract_phone,contract_name,product_num,price) VALUES (%s,%s,'%s',%s,%s,%s) returning id
                        """ % (
                        valus.get('name'),valus.get('partner_id'),contract_phone,valus.get('contract_name',False),valus.get('product_num'),price)
                        cr.execute(sql)
                        return_obj = cr.fetchall()
                        res_ids.append(return_obj[0][0])
                else:
                    valus['product_num'] = 0.0
                    valus['price'] = pricelist_obj.price_get(cr, uid, [supplierinfo_id.name.property_product_pricelist_purchase.id],
                        product_id.id, 1.0, supplierinfo_id.name.id, {
                    'uom': product_id.uom_po_id.id,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    })[supplierinfo_id.name.property_product_pricelist_purchase.id]
                    if not valus.get('price'):
                        price = 0.0
                    else:
                        price = valus['price']
                    if not valus.get('contract_phone'):
                        contract_phone = False
                    else:
                        contract_phone = valus.get('contract_phone')
                    sql = """
                        insert into qdodoo_product_supplierinfo (name,partner_id,contract_phone,contract_name,product_num,price) VALUES (%s,%s,'%s',%s,%s,%s) returning id
                        """ % (
                        valus.get('name'),valus.get('partner_id'),contract_phone,valus.get('contract_name',False),valus.get('product_num'),price)
                    cr.execute(sql)
                    return_obj = cr.fetchall()
                    res_ids.append(return_obj[0][0])
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_purchase_price', 'tree_qdodoo_product_supplierinfo')
        view_id = result and result[1] or False
        return {
              'name': ('产品供应商价格'),
              'view_type': 'form',
              "view_mode": 'tree',
              'res_model': 'qdodoo.product.supplierinfo',
              'type': 'ir.actions.act_window',
              'view_id': [view_id],
        }




