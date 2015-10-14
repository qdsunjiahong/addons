# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api


# import time
# from openerp.tools.translate import _
# from datetime import timedelta, datetime
#  import logging
# from openerp import SUPERUSER_ID

# _logger = logging.getLogger(__name__)

class qdodoo_protask_over(models.Model):
    """
    命名规则：
        1、优先级到5星
        2、追加状态 a开始b完成c取消
    """
    # _name = 'tet.template.line'    # 模型名称
    # _table = 'tet_template_line' # 表名，不写时以name为准
    # _description = 'tet.Template.line'    # 模型描述
    _inherit = 'project.task'  # 继承
    # _inherits = {'product.template': 'product_tmpl_id'}   # 多重继承
    # _order = 'name desc'    # 排序

    # 定义字段
    priority = fields.Selection(
        [('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Very High'), ('5', 'Emer')])
    state = fields.Selection([('0', 'Start'), ('1', 'Over'), ('2', 'Cancel')], default="0")

    @api.onchange('state')
    def is_over(self):
        if self.state == '1':
            if not self.date_end:
                warning = {}
                warning = {
                    'title': '结束日期必须填写',
                    'message': '请填写结束任务的日期以便查看！',
                }
                self.state = '0'
                return {'warning': warning}




                # _sql_constraints = [
                #    ('name_company_uniq', 'unique(name, company_id)', 'Tax Name must be unique per company!'),
                # ]

                # def _default_name(self, cr, uid, context=None):
                #    return False

                # _defaults = {    #默认值
                #    'state': 'draft',
                #    'name': _default_name,
                #    ……
                # }

                # def _check_name(self, cr, uid, ids, context=None):
                #    return True
                # _constraints = [
                # (_check_name, u'编号错误测试', [u'编号']),#提示信息：验证字段 编号 时发生错误：编号错误测试
                # ]
                # }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
