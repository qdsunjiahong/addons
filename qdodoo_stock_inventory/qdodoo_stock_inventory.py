# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_stock_inventory_inherit(models.Model):
    _inherit = 'stock.inventory'

    def _get_user_id(self):
        return self._uid

    user_id2 = fields.Many2one('res.users', string=u'操作人', default=_get_user_id)
