# -*- coding: utf-8 -*-
###########################################################################################
#
# module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api
from datetime import datetime
from openerp.exceptions import except_orm

class qdodoo_work_details(models.Model):
    '''
    工作日志
    '''
    _name = 'qdodoo.work.details'
    _description = 'work datails'

    name = fields.Char(string=u'日志主题')
    partner_ids = fields.Many2many('res.partner', 'work_details_res_partner', 'work_detail_id', 'partner_id',
                                   string=u'共享')
    c_date = fields.Datetime(string=u'创建日期')
    # end_date = fields.Datetime(string=u'结束日期')
    text = fields.Text(string=u'内容')
    user_id = fields.Many2one('res.users', string=u'创建者', default=lambda self: self.env.user)
    employee=fields.Many2one('hr.employee',string=u'创建员工'  ,readonly=True)


    def get_ref_user(self,cr ,uid ,context=None):
        hr_employee=self.pool.get('hr.employee')
        emp_id=hr_employee.browse(cr , 1, hr_employee.search(cr ,1 ,[('user_id','=',uid)]))
        if emp_id:
            return emp_id[0].id
        raise except_orm(('Warning!'),('注意没有关联的员工,请先关联你的员工信息！'))


    _defaults = {
        'c_date': fields.datetime.now(),
        'employee': get_ref_user,
        #  'end_date': fields.datetime.now(),
         'user_id': lambda obj, cr, uid, context: uid,
    }
