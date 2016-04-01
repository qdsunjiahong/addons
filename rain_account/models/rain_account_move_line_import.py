# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import xlrd, base64


class rain_account_move_line_import(osv.osv):
    _name = 'rain.account.move.line.import'

    _columns = {
        'account_move_id': fields.many2one('account.move', string=u'会计凭证'),
        'db_datas': fields.binary(u'Excel 文件'),
        'debit_account_id':fields.many2one('account.account', string=u'借方科目'),
        'credit_account_id':fields.many2one('account.account', string=u'贷方科目')
    }

    def action_upload(self, cr, uid, ids, context=None):
        # 处理excel
        if context is None:
            context = {}
        value = self.browse(cr, uid, ids[0]).db_datas

        debit_account_id = self.browse(cr, uid, ids[0]).debit_account_id.id
        credit_account_id = self.browse(cr, uid, ids[0]).credit_account_id.id
        account_move = self.browse(cr, uid, ids[0]).account_move_id

        context = {
            'journal_id':account_move.journal_id.id,
            'period_id':account_move.period_id.id
        }
        move_line_pool = self.pool.get('account.move.line')
        product_pool = self.pool.get('product.product')

        wb = xlrd.open_workbook(file_contents=base64.decodestring(value))
        sh = wb.sheet_by_index(0)
        nrows = sh.nrows

        for i in range(1, nrows):
            #产品 0 搜索产品
            product_id2 = None
            product_message = sh.cell(i, 0).value

            if product_message != "":
                left_index = product_message.find('[')
                right_index = product_message.find(']')
                if left_index < -1 or right_index < -1:
                    raise osv.except_osv(u'excel文件有问题',u'缺少"[",或者"]", 检查行号:%d' % (i + 1))

                product_code = product_message[left_index+1: right_index]
                product_id2 = product_pool.search(cr, uid, [('default_code', '=', product_code)])
                if not product_id2:
                    raise osv.except_osv(u'产品不存在',u' 检查行号:%d' % (i + 1))

            debit = sh.cell(i, 1).value
            credit = sh.cell(i, 2).value

            args_debit={
                'name':product_message,
                'move_id':account_move.id,
                'debit':debit,
                'credit':0.0,
                'product_id':product_id2[0],
                'account_id':debit_account_id
            }

            args_credit={
                'name':product_message,
                'move_id':account_move.id,
                'debit':0.0,
                'credit':credit,
                'product_id':product_id2[0],
                'account_id':credit_account_id
            }


            move_line_pool.create(cr, uid, args_credit, context)
            move_line_pool.create(cr, uid, args_debit, context)

rain_account_move_line_import()