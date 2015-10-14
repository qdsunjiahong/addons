#! /usr/bin/env python
# encoding:utf-8

from openerp import models, fields, api


class delete_stock_quant(models.Model):
    _name = 'delete.stock.quant'

    date_time = fields.Date(string=u'时间')

    @api.one
    def button_delete(self):
        date_time = self.date_time
        cur, location_id = self.env['ir.model.data'].get_object_reference('stock', 'stock_location_inter_wh')
