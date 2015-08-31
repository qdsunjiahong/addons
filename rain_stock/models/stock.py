# -*- coding: utf-8 -*-
from openerp.osv import  osv
class stock_production_lot(osv.osv):
        _inherit ="stock.production.lot"
        _defaults = {
        'name': lambda x, y, z, c: x.pool.get('ir.sequence').get(y, z, 'stock.lot.serial2'),
    }