# -*- coding: utf-8 -*-
from openerp.osv import fields, osv

class taylor_template(osv.Model):
    """
        在产品中添加相关价格表关联
        这样可以有效减少业务人员的操作量
    """

    _inherit = 'product.template'

    _columns = {
        'ref_pricelist_prolate':fields.one2many('pricelist.prolate.relation', 'ref_product_template',string='关联的价格表')
    }
    # 关联字段



class pricelist_prolate_relation(osv.Model):
    _name = "pricelist.prolate.relation"

    # 计算字段
    _columns = {
         "proportion" : fields.float('比例'),
        "public_price" : fields.float( string='公共价格'),
        "fixed" : fields.float('固定值'),
        "to_toal" : fields.float(string='单价', required=True),

        # 关联字段
        "ref_product_pricelist" : fields.many2one('product.pricelist', '价格表'),
        "ref_product_template" : fields.many2one('product.template', string='产品模版'),
    }

