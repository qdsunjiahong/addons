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
        tax_obj = self.env['account.tax']
        user_obj = self.env['res.users']
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
                row_n = row + 1
                data = {}
                code = str(int(sh.cell(row, 0).value))
                name = sh.cell(row, 1).value
                account_type = sh.cell(row, 2).value
                user_type = sh.cell(row, 3).value
                company_name = sh.cell(row, 4).value
                parent_account = sh.cell(row, 5).value
                reconcile = sh.cell(row, 6).value or False
                if reconcile == 'Y' or reconcile == 'y':
                    reconcile = True
                else:
                    reconcile = False
                note = sh.cell(row, 7).value or ''
                tax_ids = sh.cell(row, 8).value
                if parent_account == '':
                    parent_account = False
                else:
                    parent_account = str(int(parent_account))
                if not code:
                    raise except_orm(_(u'警告'), _(u'第%s行科目代码为空') % row_n)
                data['code'] = code
                if not name:
                    raise except_orm(_(u'警告'), _(u'第%s行科目名称为空') % row_n)
                data['name'] = name
                if not account_type:
                    raise except_orm(_(u'警告'), _(u'第%s行内部类型为空') % row_n)
                data['type'] = account_type
                if not user_type:
                    raise except_orm(_(u'警告'), _(u'第%s行类型为空') % row_n)
                if not account_type_dict.get(user_type, False):
                    raise except_orm(_(u'警告'), _(u'第%s行类型填写有误') % row_n)
                data['user_type'] = account_type_dict.get(user_type)
                if not company_name:
                    company_id_l = user_obj.browse(self.env.uid).company_id.id
                else:
                    if not company_dict.get(company_name, False):
                        raise except_orm(_(u'警告'), _(u'第%s行公司填写有误') % row_n)
                    company_id_l = company_dict.get(company_name)
                data['company_id'] = company_id_l
                if (code, company_dict.get(company_name)) in account_company_list:
                    raise except_orm(_(u'警告'), _(u'第%s行上级科目已存在') % row_n)
                if parent_account:
                    parent_id = account_dict.get((parent_account, company_id_l), False)
                    if not parent_id:
                        raise except_orm(_(u'警告'), _(u'第%s行上级科目填写有误') % row_n)
                    data['parent_id'] = parent_id
                data['reconcile'] = reconcile
                data['note'] = note
                crete_obj = account_obj.create(data)
                res_id = crete_obj.id
                account_dict[(code, company_id_l)] = res_id
                return_list.append(res_id)
                if tax_ids:
                    tax_list = tax_ids.split("/")
                    for tax_l in tax_list:
                        tax_id = tax_obj.search([('name', '=', tax_l), ('company_id', '=', company_id_l)]).id
                        sql = """
                        insert into account_account_tax_default_rel (account_id,tax_id) VALUES (%s,%s)
                        """ % (crete_obj.id, tax_id)
                        self.env.cr.execute(sql)
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
