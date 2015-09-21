# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

# from openerp import models, fields
from openerp.osv import osv, fields


class qdodoo_res_config(osv.osv):
    _inherit = "mrp.config.settings"

    _columns = {

        "module_qdodoo_mrp_materials": fields.boolean(string=u'原料消耗明细借方显示成品名称'),
    }
