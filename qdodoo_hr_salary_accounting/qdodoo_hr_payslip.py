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


class qdodoo_hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    import_file = fields.Binary(string=u'导入excel文件')
    @api.one
    def btn_import_data(self):
        excel_ids = []
        if self.import_file:
            try:
                excel_obj = xlrd.open_workbook(file_contents=base64.decodestring(self.import_file))
            except:
                raise except_orm(_(u'警告'), _(u'请使用excel文件'))
            excel_info = excel_obj.sheet_by_index(0)
            nrows = excel_info.nrows
            for row in range(1, nrows):
                if excel_info.row_values(row)[0] == self.employee_id.name and int(
                        excel_info.row_values(row)[1]) == self.employee_id.id:
                    excel_ids.append(row)
            row_new = excel_ids[0]
            if len(excel_ids) > 1:
                raise except_orm(_(u'警告'), _(u'员工%s在excel中数据出现多个') % (self.employee_id.name))

            elif not excel_ids:
                raise except_orm(_(u'警告'), _(u'员工%s在Excel中没有数据') % (self.employee_id.name))
            if self.input_line_ids:
                for line in self.input_line_ids:
                    for col in range(2, excel_info.ncols):
                        if excel_info.col_values(col)[0] == line.name:
                            line.write({'amount': excel_info.col_values(col)[row_new] or 0.0})
            else:
                raise except_orm(_(u'警告'), _(u'输入项不能为空！'))
