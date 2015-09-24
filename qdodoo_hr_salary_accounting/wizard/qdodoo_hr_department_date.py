# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, tools
import time
from datetime import datetime
from openerp.tools.translate import _
from openerp.exceptions import except_orm
from datetime import timedelta


class qdodoo_hr_dapartment_date(models.Model):
    """
    批量工资核算wizard模型，时间月份选择
    """
    _name = 'hr.department.date'

    company_id = fields.Many2one("res.company", string=u'公司')
    date = fields.Many2one('account.period', string=u'工资核算月份', required=True)
    hr_employee_ids = fields.Char(string=u'员工')

    def _default_get_company(self, cr, uid, ids, context=None):
        return self.pool.get('res.users').browse(cr, uid, uid).company_id.id

    def _default_get_employee(self, cr, uid, context=None):
        employee_ids = ''
        # print context
        if context.get('active_model') == 'hr.employee':
            active_ids = context.get('active_ids', []) or []
            employee_obj = self.pool.get('hr.employee')
            for line in employee_obj.browse(cr, uid, active_ids, context=context):
                employee_ids += str(line.id) + ';'
            return employee_ids[0:-1]

    def _get_period(self, cr, uid, context=None):
        ctx = dict(context or {})
        date_now = fields.datetime.today()
        date_now = str(date_now)
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=ctx)
        company_id = user_obj.company_id.id
        date_now_new = date_now[:5] + str(int(date_now[5:7]) - 1) + date_now[7:10]
        period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', date_now_new),
                                                                      ('date_stop', '>=', date_now_new),
                                                                      ('company_id', '=', company_id)])

        return period_ids[0]

    _defaults = {
        'company_id': _default_get_company,
        'hr_employee_ids': _default_get_employee,
        'date': _get_period
    }

    @api.one
    def action_done(self):
        create_list = []
        employee_ids = self.hr_employee_ids.split(';')
        for employee_id in employee_ids:
            employee_id = int(employee_id)
            employee_obj = self.env['hr.employee'].browse(employee_id)
            date_from = self.date.date_start
            date_to = self.date.date_stop
            company_id = employee_obj.company_id.id
            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_to, "%Y-%m-%d")))
            name = _('Salary Slip of %s for %s') % (employee_obj.name, tools.ustr(ttyme.strftime('%B-%Y')))
            contract_ids = self.env['hr.payslip'].get_contract(employee_obj, date_from, date_to)
            if contract_ids:
                contract_record = self.env['hr.contract'].browse(contract_ids[0])
                contract_id = contract_record.id
                struct_id = contract_record.struct_id.id
                hr_department_id = contract_record.hr_department_id.id
            else:
                raise except_orm(_(u'警告！'), _(u'员工%s未创建合同') % (employee_obj.name))
            hr_user_id = employee_obj.user_id.id
            # worked_days_line_ids = self.env['hr.payslip'].get_worked_day_lines(contract_ids, date_from, date_to)
            input_line_ids = self.get_inputs(contract_ids, date_from, date_to)
            model_data = self.env['ir.model.data']
            res = model_data.search([('name', '=', 'expenses_journal')])
            if res:
                journal_id = model_data.browse(res[0]).res_id
            else:
                journal_id = False
            create_dict = {'employee_id': employee_id, 'date_from': date_from, 'date_to': date_to,
                           'name': name, 'hr_user_id': hr_user_id, 'contract_id': contract_id,
                           'struct_id': struct_id, 'hr_department_id': hr_department_id,
                           'company_id': company_id, 'journal_id': journal_id, 'state': 'draft',
                           'input_line_ids': input_line_ids}
            create_list.append(create_dict)
        for i in create_list:
            self.env['hr.payslip'].create(i)

    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = []
        contract_obj = self.pool.get('hr.contract')
        rule_obj = self.pool.get('hr.salary.rule')
        contract_obj_new = contract_obj.browse(cr, uid, contract_ids[0])
        structure_ids = contract_obj.get_all_structures(cr, uid, contract_ids, context=context)
        if not structure_ids:
            raise except_orm(_(u'警告'), _(u'员工%s的合同没有关联工资结构') % (contract_obj_new.employee_id.name))
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            for rule in rule_obj.browse(cr, uid, sorted_rule_ids, context=context):
                if rule.input_ids:
                    for input in rule.input_ids:
                        industry_accounting_ids = self.pool.get('industry.accounting.line').search(cr, uid, [
                            ('name', '=', input.name), ('contract_id', '=', contract.id)])
                        if not industry_accounting_ids:
                            raise except_orm(_(u'警告'),
                                             _(u'员工%s的工资规则%s未创建') % (contract.employee_id.name, input.name))
                        elif len(industry_accounting_ids) > 1:
                            raise except_orm(_(u'警告'), _(u'员工%s工资核算中的工资规则%s出现重复') % (
                                contract.employee_id.name, input.name))
                        industry_accounting_obj = self.pool.get('industry.accounting.line').browse(cr, uid,
                                                                                                   industry_accounting_ids[
                                                                                                       0])

                        inputs = {
                            'name': input.name,
                            'amount': industry_accounting_obj.qty,
                            'code': input.code,
                            'contract_id': contract.id,
                        }
                        res.append((0, 0, inputs))
        return res
