# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_hr_employee_inherit(models.Model):
    _inherit = 'hr.employee'
    '''
    人力资源》员工，增加onchange方法
    '''

    def onchange_job_id(self, cr, uid, ids, job_id, context=None):
        if job_id:
            contract_ids = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', ids[0])], context=context)
            for line in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
                line.write({'job_id': job_id})

    def onchange_department_id(self, cr, uid, ids, department_id, context=None):
        value = {'parent_id': False}
        if department_id:
            contract_ids = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', ids[0])], context=context)
            for line in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
                line.write({'hr_department_id': department_id})
            department = self.pool.get('hr.department').browse(cr, uid, department_id)
            value['parent_id'] = department.manager_id.id
        return {'value': value}


class qdodoo_hr_contract_inherit(models.Model):
    _inherit = 'hr.contract'
    '''
    人力资源》合同,增加onchange方法
    '''

    def onchange_job_department_id(self, cr, uid, ids, job_id, hr_department_id, employee_id, context=None):
        employee_obj = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
        employee_obj.write({'job_id': job_id, 'department_id': hr_department_id})
