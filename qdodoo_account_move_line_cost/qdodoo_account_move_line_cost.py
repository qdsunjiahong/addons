# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('debit', 'credit')
    def check_onchange(self):
        if self.debit > 0 and self.credit > 0:
            raise except_orm(_(u'警告'), _(u'同一行借方和贷方只能有一个大于0！'))
        else:
            pass

    @api.constrains('debit', 'credit')
    def _check_de_cr(self):
        if self.debit > 0 and self.credit:
            raise ValueError(_(u'借方喝贷方只能有一个大于0！'))
