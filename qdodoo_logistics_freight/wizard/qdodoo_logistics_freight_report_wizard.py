# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_logistics_freight_report_wizard(models.Model):
    _name = 'qdodoo.logistics.freight.report.wizard'
    _description = 'qdodoo.logistics.freight.report.wizard'

    start_date = fields.Date(string=u'开始时间')
    end_date = fields.Date(string=u'结束时间')

    @api.multi
    def action_done(self):
        report_obj = self.env['purchase.order']
        mod_obj = self.env['ir.model.data']
        result_list = []
        pass
