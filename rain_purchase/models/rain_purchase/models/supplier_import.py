# -*- coding: utf-8 -*-


from openerp.osv import fields, osv
import xlrd, base64
from openerp.tools.translate import _
import sys
import types


class rain_supplier_import(osv.osv):
    _name = 'rain.supplier.import'

    _columns = {
        'db_datas' : fields.binary('Database Data'),
    }

    def action_upload(self, cr, uid, ids, context=None):
        '''
            上传xls文件，导入供应商信息
        :param cr:
        :param uid:
        :param ids:
        :param context:
        :return:
        '''

        value = self.browse(cr, uid, ids[0]).db_datas
        wb = xlrd.open_workbook(file_contents=base64.decodestring(value))
        sh = wb.sheet_by_index(0)
        nrows = sh.nrows


        for rownum in range(3,nrows):

            #内部备注　５

            #编码     6

            #联系人　 9

            #付款方式　10

            pass

rain_supplier_import()