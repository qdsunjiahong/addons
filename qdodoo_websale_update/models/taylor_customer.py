# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import fields, osv, orm
from openerp import SUPERUSER_ID
from openerp.addons.web.http import request
from openerp.tools.translate import _

class taylor_customer(osv.Model):
    """
        在客户中添加出库仓库
        在生成采购订单时 直接设置仓库 为客户中的仓库
    """

    _inherit = 'res.partner'    # 继承客户数据模型

    _columns = {    # 定义字段
        'out_stock': fields.many2one('stock.warehouse','仓库'),
        'location_id': fields.many2one('stock.location', '出库库位'),
        'assist_pricelist': fields.many2one('product.pricelist',u'网络报货辅助价格表'),
    }

    def change_out_stock_id(self, cr, uid, ids, out_stock, context=None):
        if out_stock:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, out_stock, context=context)
            return {'value': {'location_id': warehouse.lot_stock_id.id}}
        return {}

class qdodoo_website(orm.Model):
    _inherit = 'website'

    def sale_get_order(self, cr, uid, ids, force_create=False, code=None, update_pricelist=None, context=None):
        sale_order_obj = self.pool['sale.order']
        if uid == 3:
            sale_order_id = request.session.get('sale_order_id')
        else:
            sale_order_id = sale_order_obj.search(cr, uid, [('is_website','=',True),('state','=','draft')])
        sale_order = None
        # create so if needed
        if not sale_order_id and (force_create or code):
            # TODO cache partner_id session
            partner = self.pool['res.users'].browse(cr, uid, uid, context=context).partner_id
            for w in self.browse(cr, uid, ids):
                values = {
                    'user_id': w.user_id.id,
                    'order_policy': 'manual',
                    'is_website':True,
                    'partner_id': partner.id,
                    'pricelist_id': partner.property_product_pricelist.id,
                    'section_id': self.pool.get('ir.model.data').get_object_reference(cr, uid, 'website', 'salesteam_website_sales')[1],
                }
                sale_order_id = sale_order_obj.create(cr, uid, values, context=context)
                values = sale_order_obj.onchange_partner_id(cr, SUPERUSER_ID, [], partner.id, context=context)['value']
                sale_order_obj.write(cr, SUPERUSER_ID, [sale_order_id], values, context=context)
                request.session['sale_order_id'] = sale_order_id
        if sale_order_id:
            sale_order_id = sale_order_id[0]
            # TODO cache partner_id session
            partner = self.pool['res.users'].browse(cr, uid, uid, context=context).partner_id

            sale_order = sale_order_obj.browse(cr, SUPERUSER_ID, sale_order_id, context=context)
            if not sale_order.exists():
                request.session['sale_order_id'] = None
                return None

            # check for change of pricelist with a coupon
            if code and code != sale_order.pricelist_id.code:
                pricelist_ids = self.pool['product.pricelist'].search(cr, SUPERUSER_ID, [('code', '=', code)], context=context)
                if pricelist_ids:
                    pricelist_id = pricelist_ids[0]
                    request.session['sale_order_code_pricelist_id'] = pricelist_id
                    update_pricelist = True
            pricelist_id = request.session.get('sale_order_code_pricelist_id') or partner.property_product_pricelist.id
            # check for change of partner_id ie after signup
            if sale_order.partner_id.id != partner.id and request.website.partner_id.id != partner.id:
                flag_pricelist = False
                if pricelist_id != sale_order.pricelist_id.id:
                    flag_pricelist = True
                fiscal_position = sale_order.fiscal_position and sale_order.fiscal_position.id or False

                values = sale_order_obj.onchange_partner_id(cr, SUPERUSER_ID, [sale_order_id], partner.id, context=context)['value']
                if values.get('fiscal_position'):
                    order_lines = map(int,sale_order.order_line)
                    values.update(sale_order_obj.onchange_fiscal_position(cr, SUPERUSER_ID, [],
                        values['fiscal_position'], [[6, 0, order_lines]], context=context)['value'])

                values['partner_id'] = partner.id
                sale_order_obj.write(cr, SUPERUSER_ID, [sale_order_id], values, context=context)

                if flag_pricelist or values.get('fiscal_position', False) != fiscal_position:
                    update_pricelist = True
            if pricelist_id != sale_order.pricelist_id.id:
                update_pricelist = True
            # update the pricelist
            if update_pricelist:
                values = {'pricelist_id': pricelist_id}
                values.update(sale_order.onchange_pricelist_id(pricelist_id, None)['value'])
                sale_order.write(values)
                for line in sale_order.order_line:
                    sale_order._cart_update(product_id=line.product_id.id, line_id=line.id, add_qty=0)

            # update browse record
            if (code and code != sale_order.pricelist_id.code) or sale_order.partner_id.id !=  partner.id:
                sale_order = sale_order_obj.browse(cr, SUPERUSER_ID, sale_order.id, context=context)
        return sale_order



