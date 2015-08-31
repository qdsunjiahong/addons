# -*- coding: utf-8 -*-
###############
#from openerp import api,models,_,fields 必须添加
###############

from openerp import api,models,_,fields

class payment_supplier (models.Model):
        # 继承哪个类
        _inherit="payment.order"

        # 定义一个需要显示的字段、fields的类型为many2one 。显示的对象、显示的名字、知否必填、筛选条件required
        payment_supplier = fields.Many2one("res.partner","supplier",required=True,domain=[("supplier","=",True)])
        payment_supplier_comment = fields.Text("comment")

        @api.onchange('payment_supplier')
        def _onchange_payment_order(self):
            self.payment_supplier_comment = self.payment_supplier.comment
