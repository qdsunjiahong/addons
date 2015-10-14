# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class store_deposit(models.Model):
    _name = "store.deposit"

    name = fields.Char( string='名称', readonly=True)
    deposit_time = fields.Datetime(string='存款时间', required=True)
    locat_deposit = fields.Char('地点', required=True)
    money = fields.Float(string='金额', digits=(20, 2), required=True)
    remarks = fields.Text(string='备注')

    def _get_user(self, cr, uid, ids, context=None):
        #print '111111111111111111'
        user = self.pool.get('res.users')
        return user.browse(cr, uid, uid).name

    _defaults = {
        'name': _get_user,
    }
