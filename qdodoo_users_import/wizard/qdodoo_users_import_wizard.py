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
    _name = 'qdodoo.users.import'
    _description = 'qdodoo.users.import'

    excel_file = fields.Binary(string=u'文件', required=True)

    @api.multi
    def action_import(self):
        # 打开文件，获取文件对象
        excel_obj = xlrd.open_workbook(file_contents=base64.decodestring(self.excel_file))
        sheets = excel_obj.sheets()
        data_obj = self.env['ir.model.data']
        user_obj = self.env['res.users']
        # 获取当前用户所属公司
        company_ids = self.env['res.company'].search([])
        # 公司字典{'company_name':company_id}
        company_dict = {}
        for company_l in company_ids:
            company_dict[company_l.name] = company_l.id
        return_list = []
        for sh in sheets:
            for row in range(2, sh.nrows):
                row_n = row + 1
                data = {}
                name = sh.cell(row, 0).value
                emial = sh.cell(row, 1).value
                company_name = sh.cell(row, 2).value
                password = sh.cell(row, 3).value
                company_names = sh.cell(row, 4).value
                if not isinstance(name, unicode):
                    name = str(name)
                if not isinstance(emial, unicode):
                    emial = emial
                if not isinstance(company_name, unicode):
                    company_name = str(company_name)
                if not isinstance(password, unicode):
                    password = str(password)
                if not isinstance(company_names, unicode):
                    company_names = str(company_names)
                if not name or not emial:
                    raise except_orm(_(u'警告'), _(u'第%s行有必填项为空') % row_n)
                data['name'] = name
                data['login'] = emial
                if company_name:
                    data['company_id'] = company_dict.get(company_name)
                if password:
                    data['password'] = password
                create_obj = user_obj.create(data)
                create_id = create_obj.id
                if company_names:
                    for company_l in company_names.split("/"):
                        if company_dict.get(company_l) != create_id.compamy_id.id:
                            sql = """
                            insert into res_company_users_rel (user_id,cid) VALUES (%s,%s)
                            """ % (create_id, company_dict.get(company_l))
                            self.env.cr.execute(sql)
                return_list.append(create_id)

        if return_list:
            tree_model, tree_id = data_obj.get_object_reference('base', 'view_users_tree')
            form_model, form_id = data_obj.get_object_reference('base', 'view_users_form')
            return {
                'name': _(u'科目'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'res.users',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', return_list)],
                'views': [(tree_id, 'tree'), (form_id, 'form')],
                'view_id': [tree_id],
            }
        else:
            raise except_orm(_(u'警告'), _(u'导入出错'))
