# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_account_invoice(models.Model):
    _inherit = 'stock.invoice.onshipping'

    def _compute_date(self):
        return fields.date.today()

    invoice_date = fields.Date(string=u'发票日期', default=_compute_date)
