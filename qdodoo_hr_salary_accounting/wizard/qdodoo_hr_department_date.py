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
    journal_id = fields.Many2one('account.journal', string=u'工资分录', required=True)
    number = fields.Selection([(1, 1),
                               (2, 2),
                               (3, 3)], string=u'工资发放序列号', required=True)
    hr_employee_ids = fields.Char(string=u'员工ID')
    industry_accounting_ids = fields.Char(string=u'工资核算项ID')

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

    def _default_industry_accounting_ids(self, cr, uid, context=None):
        employee_ids = ''
        if context.get('active_model') == 'qdodoo.industry.accounting':
            active_ids = context.get('active_ids', []) or []
            employee_obj = self.pool.get('qdodoo.industry.accounting')
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
        if period_ids:

            return period_ids[0]
        else:
            return False

    def _defaul_get_journal_id(self, cr, uid, context=None):
        model_data = self.pool.get('ir.model.data')
        res = model_data.search(cr, uid, [('name', '=', 'expenses_journal')])
        if res:
            return model_data.browse(cr, uid, res[0]).res_id
        return False

    _defaults = {
        'company_id': _default_get_company,
        'hr_employee_ids': _default_get_employee,
        'date': _get_period,
        'journal_id': _defaul_get_journal_id,
        'industry_accounting_ids': _default_industry_accounting_ids,
    }

    @api.multi
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
            input_line_ids = self.get_inputs(contract_ids, self.date.id, self.number)
            journal_id = self.journal_id.id
            hr_ids = self.env['hr.payslip'].search(
                [('employee_id', '=', employee_id), ('date_from', '=', date_from), ('date_to', '=', date_to),
                 ('state', '!=', 'cancel'), ('number_l', '=', self.number)])
            if hr_ids:
                raise except_orm(_(u'警告'), _(u'员工%s的当前期间工资条已存在') % (employee_obj.name))
            create_dict = {'employee_id': employee_id, 'date_from': date_from, 'date_to': date_to,
                           'name': name, 'hr_user_id': hr_user_id, 'contract_id': contract_id,
                           'struct_id': struct_id, 'hr_department_id': hr_department_id,
                           'company_id': company_id, 'journal_id': journal_id, 'state': 'draft',
                           'number_l': self.number,
                           'input_line_ids': input_line_ids}
            create_list.append(create_dict)
        i_list = []
        for i in create_list:
            cre_obj = self.env['hr.payslip'].create(i)
            i_list.append(cre_obj.id)

        mod_obj = self.env['ir.model.data']

        inv_ids = i_list
        for inv_i in self.env['hr.payslip'].browse(inv_ids):
                inv_i.compute_sheet()
                pass
        if len(inv_ids) > 0:
            mo, view_id = mod_obj.get_object_reference('hr_payroll', 'view_hr_payslip_tree')
            mo_form, view_id_form = mod_obj.get_object_reference('hr_payroll', 'view_hr_payslip_form')
            return {
                'name': _('员工工资条'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'hr.payslip',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', inv_ids)],
                'views': [(view_id, 'tree'), (view_id_form, 'form')],
                'view_id': [view_id],
            }
        else:
            raise except_orm(_(u'警告'), _(u'创建工资条失败!'))

    def get_inputs(self, cr, uid, contract_ids, period_id, number_l, context=None):
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
                        print input.name,contract.id,period_id,number_l
                        industry_accounting_ids = self.pool.get('industry.accounting.line').search(cr, uid, [
                            ('name', '=', input.name), ('contract_id', '=', contract.id),
                            ('period_id', '=', period_id), ('number_l', '=', number_l)])
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

    @api.multi
    def action_done2(self):
        employee_ids = []
        create_list = []
        number_list = []
        industry_accounting_list = []
        industry_accounting_ids = self.industry_accounting_ids.split(';')
        for i in industry_accounting_ids:
            industry_accounting_list.append(int(i))
        for industry_accounting_id in self.env['qdodoo.industry.accounting'].browse(industry_accounting_list):
            employee_ids.append(industry_accounting_id.employee_id.id)
            number_list.append(industry_accounting_id.number)
        if len(list(set(number_list))) > 1:
            raise except_orm(_(u'警告'), _(u'一次只能选择相同序列号'))
        for employee_id in employee_ids:
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
            print contract_ids, self.number
            input_line_ids = self.get_inputs(contract_ids, self.date.id, self.number)
            journal_id = self.journal_id.id
            hr_ids = self.env['hr.payslip'].search(
                [('employee_id', '=', employee_id), ('date_from', '=', date_from), ('date_to', '=', date_to),
                 ('state', '!=', 'cancel'), ('number_l', '=', self.number)])
            if hr_ids:
                raise except_orm(_(u'警告'), _(u'员工%s的当前期间工资条已存在') % (employee_obj.name))
            create_dict = {'employee_id': employee_id, 'date_from': date_from, 'date_to': date_to,
                           'name': name, 'hr_user_id': hr_user_id, 'contract_id': contract_id,
                           'struct_id': struct_id, 'hr_department_id': hr_department_id,
                           'company_id': company_id, 'journal_id': journal_id, 'state': 'draft',
                           'number_l': self.number,
                           'input_line_ids': input_line_ids}
            create_list.append(create_dict)
        i_list = []
        for i in create_list:
            cre_obj = self.env['hr.payslip'].create(i)
            i_list.append(cre_obj.id)

        mod_obj = self.env['ir.model.data']

        inv_ids = i_list
        for inv_i in self.env['hr.payslip'].browse(inv_ids):
            inv_i.compute_sheet()
        if len(inv_ids) > 0:
            mo, view_id = mod_obj.get_object_reference('hr_payroll', 'view_hr_payslip_tree')
            mo_form, view_id_form = mod_obj.get_object_reference('hr_payroll', 'view_hr_payslip_form')
            return {
                'name': _('员工工资条'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'hr.payslip',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', inv_ids)],
                'views': [(view_id, 'tree'), (view_id_form, 'form')],
                'view_id': [view_id],
            }
        else:
            raise except_orm(_(u'警告'), _(u'创建工资条失败!'))
