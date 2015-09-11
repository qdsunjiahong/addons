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

from openerp.osv import osv,fields

class hm_product_export(osv.Model):
    _name="product.template"
    _inherit='product.template'

    def _get_main_supplier(self,cr,uid,ids,name,args,context=None):
        res={}
        for id in ids:
		product_tempalte = self.browse(cr,uid,id,context=context)
                if product_tempalte.seller_ids:
		    for supplier in product_tempalte.seller_ids:
		        res[id] = supplier.name.name
                else:
                    res[id]=""
        return res

    _columns={
            "main_supplier":fields.function(_get_main_supplier,string='Main Supplier',type="char",method=True)
            }

