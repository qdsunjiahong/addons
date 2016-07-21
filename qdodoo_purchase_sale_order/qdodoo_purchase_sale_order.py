# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv.osv import except_osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class qdodoo_purchase_sale_order(models.Model):
    """
        多公司根据采购单触发销售单
    """
    _inherit = 'purchase.order'  # 继承

    location_name = fields.Many2one('stock.warehouse', u'仓库')
    is_internal_company = fields.Boolean(u'是否是内部公司')
    mail_users = fields.Many2one('res.users', u'发件人')

    def wkf_send_rfq(self, cr, uid, ids, context=None):
        res = super(qdodoo_purchase_sale_order, self).wkf_send_rfq(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'mail_users': uid})
        return res

    def action_picking_create(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids):
            picking_vals = {
                'picking_type_id': order.picking_type_id.id,
                'partner_id': order.partner_id.id,
                'date': order.date_order,
                'origin': order.name,
                'company_id': order.company_id.id
            }
            picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
            self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)

    def onchange_partner_id2(self, cr, uid, ids, partner_id, company, context=None):
        partner = self.pool.get('res.partner')
        if not partner_id:
            return {'value': {
                'fiscal_position': False,
                'payment_term_id': False,
            }}

        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        user_ids = self.pool.get('res.users').search(cr, uid, [('company_id', '=', company)])
        if user_ids:
            uid = user_ids[0]
        if not company_id:
            raise except_osv(_('Error!'), _('There is no default company for the current user!'))
        fp = self.pool['account.fiscal.position'].get_fiscal_position(cr, uid, company_id, partner_id, context=context)
        supplier_address = partner.address_get(cr, uid, [partner_id], ['default'], context=context)
        supplier = partner.browse(cr, uid, partner_id, context=context)
        return {'value': {
            'is_internal_company': supplier.is_internal_company,
            'pricelist_id': supplier.property_product_pricelist_purchase.id,
            'fiscal_position': fp or supplier.property_account_position and supplier.property_account_position.id,
            'payment_term_id': supplier.property_supplier_payment_term.id or False,
        }}

    def copy_product_company(self, cr, uid):
        template_obj = self.pool.get('product.template')
        template_ids = template_obj.search(cr, uid, [('company_id', '=', 1)])
        for line in template_obj.browse(cr, uid, template_ids):
            res_id = template_obj.copy(cr, uid, line.id, {'company_id': 4})
            template_obj.write(cr, uid, res_id, {'name': line.name, 'default_code': line.default_code})
        return True

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        super(qdodoo_purchase_sale_order, self).wkf_confirm_order(cr, uid, ids, context=context)
        sale_obj = self.pool.get('sale.order')
        product_obj = self.pool.get('product.product')
        sale_line_obj = self.pool.get('sale.order.line')
        partner_obj = self.pool.get('res.partner')
        company_obj = self.pool.get('res.company')
        # 获取数据字典{客户id：公司id}
        dict_partner_company = {}
        dict_partner_company_name = {}
        for lines in company_obj.browse(cr, 1, company_obj.search(cr, 1, [])):
            dict_partner_company[lines.partner_id.id] = lines.id
            dict_partner_company_name[lines.partner_id.id] = lines.name
        for obj in self.browse(cr, uid, ids):
            # 如果客户是内部公司
            if obj.partner_id.is_internal_company:
                part_id = obj.company_id.partner_id.id
                project_id = obj.partner_id.analytic_account_id.id
                if not project_id:
                    raise except_osv(_(u'警告'), _(u'%s的辅助核算项未填') % obj.partner_id.name)
                part = partner_obj.browse(cr, uid, part_id, context=context)
                addr = partner_obj.address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
                pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
                invoice_part = partner_obj.browse(cr, uid, addr['invoice'], context=context)
                payment_term = invoice_part.property_payment_term and invoice_part.property_payment_term.id or False
                dedicated_salesman = part.user_id and part.user_id.id or uid
                delivery_onchange = sale_obj.onchange_delivery_id(cr, uid, ids, False, part.id, addr['delivery'], False,
                                                                  context=context)
                val = {
                    'partner_id': part_id,
                    'company_id': dict_partner_company.get(obj.partner_id.id, ''),
                    'partner_invoice_id': addr['invoice'],
                    'partner_shipping_id': addr['delivery'],
                    'payment_term': payment_term,
                    'user_id': dedicated_salesman,
                    'location_id_note': obj.name + ':' + obj.picking_type_id.warehouse_id.name + ':' + obj.picking_type_id.name,
                    'warehouse_id': obj.location_name.id,
                    'project_id': project_id,
                }
                val.update(delivery_onchange['value'])
                if pricelist:
                    val['pricelist_id'] = pricelist
                if not sale_obj._get_default_section_id(cr, uid, context=context) and part.section_id:
                    val['section_id'] = part.section_id.id
                sale_note = sale_obj.get_salenote(cr, uid, ids, part.id, context=context)
                if sale_note:
                    val.update({'note': sale_note})
                res_id = sale_obj.create(cr, 1, val)
                for line in obj.order_line:
                    product_ids = product_obj.search(cr, 1, [('default_code', '=', line.product_id.default_code), (
                        'company_id', '=', dict_partner_company.get(obj.partner_id.id, ''))])
                    if not product_ids:
                        raise except_osv(_('警告!'), _('%s没有设置%s数据!') % (
                            dict_partner_company_name.get(obj.partner_id.id, ''), line.product_id.name))
                    product_obj_obj = product_obj.browse(cr, uid, product_ids[0])
                    sale_line_obj.create(cr, 1, {
                        'order_id': res_id,
                        'product_id': product_obj_obj.id,
                        'product_uom_qty': line.product_qty,
                        'price_unit': line.price_unit,
                    })
                res_users = self.pool.get('res.users').search(cr, 1, [('company_id','=',dict_partner_company.get(obj.partner_id.id, ''))])
                sale_obj.action_button_confirm(cr, res_users[0], [res_id])
        return True


class qdodoo_res_partner_inherit(models.Model):
    """
        业务伙伴增加是否是内部公司
    """
    _inherit = 'res.partner'  # 继承

    is_internal_company = fields.Boolean(u'是否是内部公司')


class qdodoo_sale_order_inherit(models.Model):
    """
        销售单中增加目的仓库的备注
    """
    _inherit = 'sale.order'  # 继承

    location_id_note = fields.Char(u'目的仓库备注')
    mail_users = fields.Many2one('res.users', u'发件人')

    def action_quotation_send(self, cr, uid, ids, context=None):
        res = super(qdodoo_sale_order_inherit, self).action_quotation_send(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'mail_users': uid})
        return res
