# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models
from openerp.osv import osv
import time
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_stock_picking_wave(models.Model):
    """
        波次负责人增加默认值
    """
    _inherit = 'stock.picking.wave'    # 继承

    user_id = fields.Many2one('res.users', 'Responsible', help='Person responsible for this wave')

    _defaults = {
       'user_id':lambda self, cr, uid, ids, context=None:uid,
    }

    def print_picking_all(self, cr, uid, ids, context=None):
        '''
            整合打印
        '''
        context = dict(context or {})
        info_obj = self.pool.get('qdodoo.report.info')
        # users_obj = self.pool.get('res.users')
        # company_lst = []
        # 获取当前登录人可以看到的公司信息
        # for company_id in users_obj.browse(cr, uid, uid).company_ids:
        #     company_lst.append(company_id.id)
        info_obj_ids = info_obj.search(cr, uid, [])
        info_obj.unlink(cr, uid, info_obj_ids)
        ids_lst = []
        for wave in self.browse(cr, uid, ids, context=context):
            for picking in wave.picking_ids:
                for line_id in picking.move_lines:
                    info_obj_new_ids = info_obj.search(cr, uid, [('product_id','=',line_id.product_id.id)])
                    if info_obj_new_ids:
                        info_obj_obj = info_obj.browse(cr, uid, info_obj_new_ids[0])
                        info_obj.write(cr, uid, info_obj_new_ids[0], {'qty':info_obj_obj.qty + line_id.product_uom_qty})
                    else:
                        res_id = info_obj.create(cr, uid, {'product_id':line_id.product_id.id,'qty':line_id.product_uom_qty,
                                              'product_uom_id':line_id.product_uom.id})
                        ids_lst.append(res_id)
        if not ids_lst:
            raise osv.except_osv(_('警告!'), _(u'没有打印的内容！'))
        context['active_ids'] = ids_lst
        context['active_model'] = 'qdodoo.report.info'
        return self.pool.get("report").get_action(cr, uid, [], 'qdodoo_picking_wave.qdodoo_report_picking', context=context)

class qdodoo_report_info(models.Model):
    _name = 'qdodoo.report.info'

    product_id = fields.Many2one('product.product',u'产品')
    qty = fields.Float(u'数量')
    product_uom_id = fields.Many2one('product.uom',u'单位')

class qdodoo_res_partner_inherit(models.Model):
    _inherit = 'res.partner'

    delivery_id = fields.Many2one('delivery.carrier',u'承运方')

class qdodoo_stock_picking_inherit(models.Model):
    _inherit = 'stock.picking'

    # 获取承运方
    def onchange_get_delivery_id(self, cr, uid, ids, partner_id=None, context=None):
        if not partner_id:
            return {}
        partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        warning = {}
        title = False
        message = False
        if partner.picking_warn != 'no-message':
            title = _("Warning for %s") % partner.name
            message = partner.picking_warn_msg
            warning = {
                'title': title,
                'message': message
            }
            if partner.picking_warn == 'block':
                return {'value': {'partner_id': False}, 'warning': warning}

        result = {'value': {}}
        if partner.delivery_id:
            result = {'value':{'shipper':partner.delivery_id.id}}
        else:
            result = {'value':{'shipper':''}}

        if warning:
            result['warning'] = warning
        return result

    # 创建时如果业务伙伴有承运方即可关联上
    def create(self, cr, uid, valus, context=None):
        if valus.get('partner_id'):
            partner = self.pool.get('res.partner').browse(cr, uid, valus.get('partner_id'), context=context)
            if partner.delivery_id:
                valus['shipper'] = partner.delivery_id.id
        return super(qdodoo_stock_picking_inherit, self).create(cr, uid, valus, context=context)

