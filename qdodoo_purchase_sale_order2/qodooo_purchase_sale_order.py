# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from openerp import models, fields,_, api
from openerp.osv.osv import except_osv

class qdodoo_sale_order_inherit(models.Model):
    """
        销售单中增加目的仓库的备注
    """
    _inherit = 'sale.order'  # 继承

    # location_id_note = fields.Char(u'目的仓库备注')
    project_id = fields.Many2one('account.analytic.account', 'Contract / Analytic', readonly=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                 required=True, help="The analytic account related to a sales order.")

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(qdodoo_sale_order_inherit, self).onchange_partner_id(cr, uid, ids, part, context=context)
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        if part and part.analytic_account_id:
            res['value'].update({'project_id':part.analytic_account_id.id})
        return res


class qdodoo_res_partner_inherit(models.Model):
    _inherit = 'res.partner'
    """
        客户添加辅助核算项
    """
    analytic_account_id = fields.Many2one('account.analytic.account', string=u'辅助核算项')
