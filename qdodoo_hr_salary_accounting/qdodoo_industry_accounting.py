# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
import xlrd
import base64


class qdodoo_industry_accounting(models.Model):
    _name = 'qdodoo.industry.accounting'
    _rec_name = 'employee_id'

    number = fields.Selection([(1, 1),
                               (2, 2),
                               (3, 3)], string=u'工资发放序列号', required=True)
    employee_id = fields.Many2one('hr.employee', string=u'姓名', required=True)
    department_id = fields.Many2one('hr.department', string=u'部门', required=True)
    company_id = fields.Many2one('res.company', string=u'公司', required=True)
    date_time = fields.Many2one('account.period', string=u'日期', required=True)
    industry_line_ids = fields.One2many('industry.accounting.line', 'industry_accounting_id', string=u'说明')

    def onchange_emloyee_id(self, cr, uid, ids, employee_id, context=None):
        res = {}
        res['value'] = {}
        if employee_id:
            employee_obj = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
            res['value']['department_id'] = employee_obj.department_id.id
            res['value']['company_id'] = employee_obj.company_id.id
        return res


class qdodoo_industry_accounting_line(models.Model):
    _name = 'industry.accounting.line'
    name = fields.Char(string=u'说明')
    number = fields.Char(string=u'编码')
    qty = fields.Float(string=u'数量', digits=(16, 4))
    contract_id = fields.Many2one('hr.contract', string=u'合同', required=True)
    period_id = fields.Many2one('account.period', required=True, string=u'会计期间')
    number_l = fields.Selection([(1, 1),
                                 (2, 2),
                                 (3, 3)], string=u'工资发放序列号', required=True)
    industry_accounting_id = fields.Many2one('qdodoo.industry.accounting', string=u'核算项', ondelete='cascade')


class qdodoo_import_file(models.Model):
    """
    工资信息导入模型
    """
    _name = 'qdodoo.import.file'

    company_id = fields.Many2one('res.company', string=u'公司', required=True)
    number = fields.Selection([(1, 1),
                               (2, 2),
                               (3, 3)], string=u'工资发放序列号', required=True)
    date_time = fields.Many2one('account.period', string=u'日期', required=True)
    import_file = fields.Binary(string="导入的Excel文件", required=True)

    @api.multi
    def action_done(self):
        values_list = []
        values_list2 = []
        values_dict2 = {}
        if self.import_file:
            try:
                excel_obj = xlrd.open_workbook(file_contents=base64.decodestring(self.import_file))
            except:
                raise except_orm(_(u'警告'), _(u'请使用excel文件'))
            excel_info = excel_obj.sheet_by_index(0)
            nrows = excel_info.nrows
            ncols = excel_info.ncols
            date_from = self.date_time.date_start
            date_to = self.date_time.date_stop
            for row in range(1, nrows):
                row_values = excel_info.row_values(row)
                name = row_values[0]
                en_no = row_values[1]  # 修改未en_no
                en_nos = self.env['hr.employee'].search(
                    [('name', '=', name), ('e_no', '=', en_no)])
                if not len(en_nos):
                    raise except_orm(_(u'警告'), _(u'文件第%s行员工姓名或员工编号有误') % (row + 1))
                elif len(en_nos) > 1:
                    raise except_orm(_(u'警告'), _(u'员工编号为%s且员工姓名为%s搜索出多个') % (name, en_no))
                department_id = en_nos.department_id.id
                company_id = en_nos.company_id.id
                contract_ids = self.env['hr.payslip'].get_contract(en_nos, date_from, date_to)
                if contract_ids:
                    contract_record = self.env['hr.contract'].browse(contract_ids[0])
                    contract_id = contract_record.id
                else:
                    raise except_orm(_(u'警告！'), _(u'员工%s未创建合同') % (en_nos.name))
                for col in range(2, ncols):
                    industry_accounting_ids = self.env['qdodoo.industry.accounting'].search(
                        [('employee_id', '=', en_nos.id), ('date_time', '=', self.date_time.id),
                         ('number', '=', self.number)])
                    if industry_accounting_ids:
                        raise except_orm(_(u'警告'), _(u'员工%s已存在会计期为%s的工资核算项') % (en_nos.name, self.date_time.name))
                    hr_rule_obj = self.env['hr.rule.input'].search([('name', '=', excel_info.col_values(col)[0])])
                    if len(hr_rule_obj) > 1:
                        raise except_orm(_(u'警告'), _(u'工资规则%s重复创建') % (excel_info.col_values(col)[0]))
                    elif not (hr_rule_obj):
                        raise except_orm(_(u'警告'), _(u'工资规则%s未创建') % (excel_info.col_values(col)[0]))
                    else:
                        code = hr_rule_obj.code

                    values_dict2['name'] = excel_info.col_values(col)[0]
                    values_dict2['qty'] = excel_info.col_values(col)[row] or 0.0
                    values_dict2['contract_id'] = contract_id
                    values_dict2['number'] = code
                    values_dict2['period_id'] = self.date_time.id
                    values_dict2['number_l'] = self.number
                    values_list.append((0, 0, values_dict2))
                    values_dict2 = {}
                values_dict1 = {
                    'number': self.number,
                    'employee_id': en_nos.id,
                    'company_id': company_id,
                    'date_time': self.date_time.id,
                    'department_id': department_id,
                    'industry_line_ids': values_list,
                }
                values_list2.append(values_dict1)
                values_list = []
            inv_ids = []
            for line in values_list2:
                cre_obj = self.env['qdodoo.industry.accounting'].create(line)
                inv_ids.append(cre_obj.id)

            ####返回页面
            mod_obj = self.env['ir.model.data']
            if len(inv_ids) > 0:
                mo, view_id = mod_obj.get_object_reference('qdodoo_hr_salary_accounting',
                                                           'qdodoo_industry_accounting_view_tree')
                mo_form, view_id_form = mod_obj.get_object_reference('qdodoo_hr_salary_accounting',
                                                                     'qdodoo_industry_accounting_view_form')
                return {
                    'name': _('工资核算'),
                    'view_type': 'form',
                    "view_mode": 'tree,form',
                    'res_model': 'qdodoo.industry.accounting',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', inv_ids)],
                    'views': [(view_id, 'tree'), (view_id_form, 'form')],
                    'view_id': [view_id],
                }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id
    }
