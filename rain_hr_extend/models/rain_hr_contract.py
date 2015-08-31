# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
class rain_hr_contract(osv.osv):
   _inherit = 'hr.contract'
   _columns = {
       'hr_department_id' : fields.many2one('hr.department','hr_department_id'),
   }
   def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
       self.hr_department_id = self.employee_id.department_id
       if not employee_id:
           return {'value': {'job_id': False}}
       emp_obj = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
       job_id = False
       if emp_obj.job_id:
           job_id = emp_obj.job_id.id
           return {'value': {'job_id': job_id}}