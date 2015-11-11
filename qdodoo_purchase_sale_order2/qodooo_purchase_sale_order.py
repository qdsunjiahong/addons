# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields,_
from openerp.osv.osv import except_osv


class qdodoo_purchase_sale_order(models.Model):
    _inherit = 'purchase.order'

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        super(qdodoo_purchase_sale_order, self).wkf_confirm_order(cr, uid, ids, context=context)
        sale_obj = self.pool.get('sale.order')
        product_obj = self.pool.get('product.product')
        sale_line_obj = self.pool.get('sale.order.line')
        product_pricelist = self.pool.get('product.pricelist')
        partner_obj = self.pool.get('res.partner')
        company_obj = self.pool.get('res.company')
        # 获取数据字典{客户id：公司id}
        dict_partner_company = {}
        dict_partner_company_name = {}
        for lines in company_obj.browse(cr, uid, company_obj.search(cr, uid, [])):
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
                res_id = sale_obj.create(cr, uid, val)
                for line in obj.order_line:
                    product_ids = product_obj.search(cr, uid, [('default_code', '=', line.product_id.default_code), (
                        'company_id', '=', dict_partner_company.get(obj.partner_id.id, ''))])
                    if not product_ids:
                        raise except_osv(_('警告!'), _('%s没有设置%s数据!') % (
                            dict_partner_company_name.get(obj.partner_id.id, ''), line.product_id.name))
                    product_obj_obj = product_obj.browse(cr, uid, product_ids[0])
                    sale_line_obj.create(cr, uid, {
                        'order_id': res_id,
                        'product_id': product_obj_obj.id,
                        'product_uom_qty': line.product_qty,
                        'price_unit': line.price_unit,
                    })
                sale_obj.action_button_confirm(cr, uid, [res_id])
        return True


class qdodoo_sale_order_inherit(models.Model):
    """
        销售单中增加目的仓库的备注
    """
    _inherit = 'sale.order'  # 继承

    # location_id_note = fields.Char(u'目的仓库备注')
    project_id = fields.Many2one('account.analytic.account', 'Contract / Analytic', readonly=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                 required=True, help="The analytic account related to a sales order.")


class qdodoo_res_partner_inherit(models.Model):
    _inherit = 'res.partner'
    """
        客户添加辅助核算项
    """
    analytic_account_id = fields.Many2one('account.analytic.account', string=u'辅助核算项', required=True)
