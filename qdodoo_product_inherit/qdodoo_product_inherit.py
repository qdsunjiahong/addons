# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models,api
import time
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_product_template_inherit(models.Model):
    """
        增加产品编码和公司唯一性约束
    """
    _inherit = 'product.template'    # 继承

    is_create = fields.Boolean(u'是否已经创建')
    company_ids_tfs = fields.Many2many('res.company','product_company_rel','product_id','company_id',u'所属公司')

    _defaults = {
        'is_create':False,
    }

    def create(self, cr, uid, valus, context=None):
        valus['is_create'] = True
        res_id = super(qdodoo_product_template_inherit, self).create(cr, uid, valus, context=context)
        # 如果存在所属公司
        company_ids = valus.get('company_ids_tfs') and valus.get('company_ids_tfs')[0][2] or []
        company_id = valus.get('company_id')
        if company_id in company_ids:
            company_ids.remove(company_id)
        if company_ids:
            # 复制产品
            for line in company_ids:
                valus['company_id'] = line
                super(qdodoo_product_template_inherit, self).create(cr, uid, valus, context=context)
        return res_id