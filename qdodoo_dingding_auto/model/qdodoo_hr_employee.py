# encoding:utf-8

from openerp import models, fields


class qdodoo_hr_employee(models.Model):
    _inherit = 'hr.employee'

    mobile_phone = fields.Char('办公手机', readonly=False, required=True)
    dd_user_id = fields.Char(string=u'钉钉userid')
