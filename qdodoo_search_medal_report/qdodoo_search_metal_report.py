# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_medal_report(models.Model):
    _name = 'qdodoo.medal.report'

    employee_id = fields.Many2one('hr.employee', string=u'姓名')
    department_id = fields.Many2one('hr.department', string=u'部门')
    job_id = fields.Many2one('hr.job', string=u'职位')
    medal_id = fields.Many2one('gamification.badge', string=u'勋章名称')
    number = fields.Integer(string=u'数量')
    reason = fields.Char(string=u'原因')
    date = fields.Datetime(string=u'授予日期')
    user_id = fields.Char(string=u'授予人')
    invisible_field = fields.Boolean(string=u'影藏')


class qdodoo_search_medal(models.Model):
    _name = 'qdodoo.search.medal'

    def _get_company_id(self):
        return self.env['res.users'].browse(self.env.uid).company_id.id

    employee_id = fields.Many2one('hr.employee', string=u'员工')
    department_id = fields.Many2one('hr.department', string=u'部门')
    company_id = fields.Many2one('res.company', string=u'公司', default=_get_company_id)

    @api.multi
    def btn_search(self):
        badger_user_obj = self.env['gamification.badge.user']
        if (self.employee_id and not self.department_id) or (self.employee_id and self.department_id):
            return_ids = []
            medal_ids = badger_user_obj.search([('employee_id', '=', self.employee_id.id)])
            if medal_ids:
                for medal_id in medal_ids:
                    data = {
                        'department_id': self.employee_id.department_id.id,
                        'employee_id': self.employee_id.id,
                        'job_id': self.employee_id.job_id.id,
                        'medal_id': medal_id.badge_id.id,
                        'number': 1,
                        'reason': medal_id.comment,
                        'date': medal_id.create_date,
                        'user_id': medal_id.sender_id.name,
                        'invisible_field': False,
                    }
                    create_obj = self.env['qdodoo.medal.report'].create(data)
                    return_ids.append(create_obj.id)

            view_model, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_search_medal_report',
                                                                                 'qdodoo_medal_report_tree')
            return {
                'name': _('勋章报表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.medal.report',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', return_ids)],
                'views': [(view_id, 'tree')],
                'view_id': [view_id],
            }
        elif not self.employee_id and self.department_id:
            medal_l = []
            medal_d = {}
            employee_ids = []
            return_ids = []
            for i in self.env['hr.employee'].search([('department_id', '=', self.department_id.id)]):
                employee_ids.append(i.id)
            if employee_ids:
                medal_ids = badger_user_obj.search([('employee_id', 'in', employee_ids)])
                for medal_id in medal_ids:
                    if medal_id.badge_id.id in medal_l:
                        medal_d[medal_id.badge_id.id] = medal_d.get(medal_id.badge_id.id, 0) + 1
                    else:
                        medal_d[medal_id.badge_id.id] = 1
                        medal_l.append(medal_id.badge_id.id)
                for medal_i in medal_l:
                    data = {
                        'department_id': self.department_id.id,
                        'medal_id': medal_i,
                        'number': medal_d.get(medal_i, 0),
                        'invisible_field': True,
                    }
                    create_obj = self.env['qdodoo.medal.report'].create(data)
                    return_ids.append(create_obj.id)
            view_model, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_search_medal_report',
                                                                                 'qdodoo_medal_report_tree2')
            return {
                'name': _('勋章报表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.medal.report',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', return_ids)],
                'views': [(view_id, 'tree')],
                'view_id': [view_id],
            }


        else:
            raise except_orm(_(u'警告'), _(u'员工和部门不能同时为空'))
