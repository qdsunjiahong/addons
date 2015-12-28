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

    company_ids_tfs = fields.Many2many('res.company','product_company_rel','product_id','company_id',u'所属公司')

    def create(self, cr, uid, valus, context=None):
        res_id = super(qdodoo_product_template_inherit, self).create(cr, uid, valus, context=context)
        if context.get('log') == 'copy':
            return res_id
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

    def write(self, cr, uid, ids, valus, context=None):
        super(qdodoo_product_template_inherit, self).write(cr, uid, ids, valus, context=context)
        if valus.get('company_ids_tfs'):
            for obj in self.browse(cr, uid, ids):
                default_code = obj.default_code
                # 获取所属公司ids
                company_ids_tfs = [obj.company_id.id]
                if obj.company_ids_tfs:
                    for line in obj.company_ids_tfs:
                        company_ids_tfs.append(line.id)
                    # 判断把没有的产品删除掉
                    company_ids_tfs_ids = self.search(cr, 1, [('default_code','=',default_code),('company_id','not in',company_ids_tfs)])
                    if company_ids_tfs_ids:
                        super(qdodoo_product_template_inherit, self).write(cr, 1, company_ids_tfs_ids, {'active':False})
                    # 判断是否所有的公司都有对应的产品(创建产品)
                    for company_id in company_ids_tfs:
                        company_ids_tfs_id = self.search(cr, 1, [('default_code','=',default_code),('company_id','=',company_id)])
                        if not company_ids_tfs_id:
                            res_id = self.copy(cr, uid, ids[0],context={'log':'copy'})
                            super(qdodoo_product_template_inherit, self).write(cr, 1, res_id, {'categ_id':1,'company_id':company_id,'default_code':default_code,'name':obj.name})
                        else:
                            super(qdodoo_product_template_inherit, self).write(cr, 1, company_ids_tfs_id, {'company_ids_tfs':obj.company_ids_tfs})
                else:
                    # 判断把没有的产品删除掉
                    company_ids_tfs_ids = self.search(cr, 1, [('default_code','=',default_code),('company_id','in',company_ids_tfs)])
                    if company_ids_tfs_ids:
                        super(qdodoo_product_template_inherit, self).write(cr, 1, company_ids_tfs_ids, {'active':False})
        return True