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

from openerp.osv import fields,osv

class hm_product_category(osv.Model):
    _inherit="product.category"

    def name_search(self,cr,user,name='',args=None,operator="ilike",context=None,limit=100):
        res=[]
        ids = self.search(cr,user,[('name',operator,name)],context=context)
        self.get_children_category(cr,user,ids,res,limit=limit,context=context)
        return self.name_get(cr,user,res,context=context)

    def get_children_category(self,cr,uid,ids,res,limit=100,context=None):
        for x_id in ids:
            children_ids = self.search(cr,uid,[('parent_id','=',x_id)],context=context)
            self.get_children_category(cr,uid,children_ids,res,limit=limit,context=context)
            res.append(x_id)