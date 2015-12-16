# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
import xlrd, base64


class qdodoo_account_import(models.Model):
    """
    科目导入wizard
    """
    _name = 'qdodoo.account.import'
    _description = 'qdodoo.account.import'

    excel_file = fields.Binary(string=u'文件', required=True)

    @api.multi
    def action_import(self):
        excel_obj = xlrd.open_workbook(file_contents=base64.decodestring(self.excel_file))
        sheets = excel_obj.sheets()
        account_obj = self.env['account.account']
        data_obj = self.env['ir.model.data']
        company_ids = self.env['res.company'].search([])
        account_type_ids = self.env['account.account.type'].search([])
        account_ids = account_obj.search([])
        account_company_list = []
        for account_id in account_ids:
            account_company_list.append((account_id.code, account_id.company_id.id))
        account_type_dict = {}
        for account_type_id in account_type_ids:
            account_type_dict[account_type_id.name] = account_type_id.id
        company_dict = {}
        return_list = []
        for company_id in company_ids:
            company_dict[company_id.name] = company_id.id
        # 科目代码：科目ID
        account_dict = {}
        for sh in sheets:
            for row in range(2, sh.nrows):
                data = {}
                code = sh.cell(row, 0).value and str(sh.cell(row, 0).value) or False
                name = sh.cell(row, 1).value or False
                account_type = sh.cell(row, 2).value or False
                user_type = sh.cell(row, 3).value or False
                company_name = sh.cell(row, 4).value or False
                parent_account = sh.cell(row, 5).value and str(sh.cell(row, 5).value) or False
                # 一级科目
                if not code:
                    raise except_orm(_(u'警告'), _(u'第%s行科目代码为空') % row)
                data['code'] = code
                if not name:
                    raise except_orm(_(u'警告'), _(u'第%s行科目名称为空') % row)
                data['name'] = name
                if not account_type:
                    raise except_orm(_(u'警告'), _(u'第%s行内部类型为空') % row)
                data['type'] = account_type
                if not user_type:
                    raise except_orm(_(u'警告'), _(u'第%s行类型为空') % row)
                if not account_type_dict.get(user_type, False):
                    raise except_orm(_(u'警告'), _(u'第%s行类型填写有误') % row)
                data['user_type'] = account_type_dict.get(user_type)
                if not company_name:
                    raise except_orm(_(u'警告'), _(u'第%s行公司为空') % row)
                if not company_dict.get(company_name, False):
                    raise except_orm(_(u'警告'), _(u'第%s行公司填写有误') % row)
                data['company_id'] = company_dict.get(company_name)
                if (code, company_dict.get(company_name)) in account_company_list:
                    raise except_orm(_(u'警告'), _(u'第%s行上级科目已存在') % row)
                if parent_account:
                    parent_id = account_dict.get(parent_account, False)
                    if not parent_id:
                        raise except_orm(_(u'警告'), _(u'第%s行上级科目填写有误') % row)
                    data['parent_id'] = parent_id
                crete_obj = account_obj.create(data)
                res_id = crete_obj.id
                account_dict[code] = res_id
                return_list.append(res_id)
        if return_list:
            tree_model, tree_id = data_obj.get_object_reference('account', 'view_account_list')
            form_model, form_id = data_obj.get_object_reference('account', 'view_account_form')
            return {
                'name': _(u'科目'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'account.account',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', return_list)],
                'views': [(tree_id, 'tree'), (form_id, 'form')],
                'view_id': [tree_id],
            }
        else:
            raise except_orm(_(u'警告'), _(u'导入出错'))
