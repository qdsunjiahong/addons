# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################
from  openerp import models,fields
import datetime
import urllib2
from lxml import etree
from openerp.tools.translate import _


class qdodoo_hr_employee(models.Model):
    """
        库存周转率
    """
    _inherit = 'hr.employee'

    # 字段定义
    work_data=fields.Integer(string='工作日志', compute='_edu_work_data')

    def _edu_work_data(self):
        '''
            计算 学历记录数量
        :return:
        '''
        Education_record = self.env['qdodoo.work.details']
        self.work_data = Education_record.search_count([('employee','=',self.id)])