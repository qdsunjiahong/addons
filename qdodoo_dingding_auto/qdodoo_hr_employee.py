# encoding:utf-8

from openerp import models, fields


class qdodoo_hr_employee(models.Model):
    _inherit = 'hr.employee'

    e_no = fields.Char(string=u'员工编号')
