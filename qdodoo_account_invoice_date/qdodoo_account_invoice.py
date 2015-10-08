# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_account_invoice(models.Model):
    _inherit = 'account.invoice'

    def _compute_date(self):
        return fields.date.today()

    date_invoice = fields.Date(string=u'发票日期', default=_compute_date)
