# -*- coding: utf-8 -*-
# #############################################################################
#
# Copyright (C) 2014 Rainsoft  (<http://www.agilebg.com>)
#    Author:Kevin Kong <kfx2007@163.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models,api,_,fields
import sys
reload(sys)

sys.setdefaultencoding('utf8')
class rainsoft_sale_order(models.Model):
    _inherit ="sale.order"

    deal_date = fields.Datetime(string="Deal Date")
    sum_qty = fields.Integer(string=u"数量合计",compute='_get_sum')
    item_qty = fields.Integer(string=u"条目合计",compute='_get_sum')

    @api.one
    def _get_sum(self):
        sum = 0
        for line in self.order_line:
            sum += line.product_uom_qty
        self.sum_qty = sum
        self.item_qty = len(self.order_line)
