# -*- coding: utf-8 -*-
# __author__ = 'sun'


import time
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp import tools, SUPERUSER_ID
from openerp.addons.product import _common

class mrp_production(osv.osv):
    _inherit = 'mrp.production'

    def action_merge(self, cr, uid, ids):
        print "************************"
        print ids
        pass


