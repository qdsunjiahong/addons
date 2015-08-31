# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import fields, osv
# import time
# from openerp.tools.translate import _
# from datetime import timedelta, datetime
# import logging
# from openerp import SUPERUSER_ID
#
# _logger = logging.getLogger(__name__)

class qdodoo_stock_inherit(osv.Model):
    """
    命名规则：
        1、若模块为自有独立模块: qdodoo_功能分类_模块名(eg:qdodoo_hr_performance)
        2、若模块为对内置模块(或三方模块)的扩展: qdodoo_内置模块名_扩展模块名(eg:qdodoo_hr_evaluation_performance)

    """
    # _name = 'tet.template.line'    # 模型名称
    #_table = 'tet_template_line' # 表名，不写时以name为准
    # _description = 'tet.Template.line'    # 模型描述
    _inherit = 'stock.picking'    # 继承
    #_inherits = {'product.template': 'product_tmpl_id'}   # 多重继承
    _order = " date desc, priority desc, id desc"
    # _order = 'name desc'    # 排序
    #
    # _columns = {    # 定义字段
    #     'name': fields.char(u'编号', size=64, readonly=True, required=True, help=u'我是编号'),
    # }

    #_sql_constraints = [
    #    ('name_company_uniq', 'unique(name, company_id)', 'Tax Name must be unique per company!'),
    #]

    #def _default_name(self, cr, uid, context=None):
    #    return False

    #_defaults = {    #默认值
    #    'state': 'draft',
    #    'name': _default_name,
    #    ……
    #}

    #def _check_name(self, cr, uid, ids, context=None):
    #    return True
    #_constraints = [
        #(_check_name, u'编号错误测试', [u'编号']),#提示信息：验证字段 编号 时发生错误：编号错误测试
    #]
   #}
class qdodoo_mrp_inherit(osv.Model):
    _inherit="mrp.production"

    _order="date_planned desc"

class qdodoo_stock_inherit(osv.Model):
    _inherit="stock.move"
    _order = "date desc"




class qdodoo_procurement_inherit(osv.Model):
    _inherit="procurement.order"

    _order = "date_planned desc,priority desc,  id asc"


