#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Designed For QingDao Xiangjie Company
#    Powered By Rainsoft(QingDao) Author:Kevin Kong 2014 (kfx2007@163.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from openerp.tools.translate import _

class rainsoft_product_category_update(osv.Model):
		_name='rainsoft.product.category.update'

		_columns={
						'property_account_creditor_price_difference_categ':fields.many2one('account.account',u'价格差异科目'),
						'property_account_income_categ':fields.many2one('account.account',u'收益科目'),
						'property_account_expense_categ':fields.many2one('account.account',u'费用科目'),
						'property_stock_account_input_categ':fields.many2one('account.account',u'入库科目'),
						'property_stock_account_output_categ':fields.many2one('account.account',u'出库科目'),
						'property_stock_valuation_account_id':fields.many2one('account.account',u'库存核算科目'),
			}
		
		def btn_ok(self,cr,uid,ids,context=None):
				if context==None:
						context={}
				categories = self.pool.get('product.category').browse(cr,uid,context.get(('active_ids'),[]),context=context)
				for category in categories:
						creditor = context.get(('property_account_creditor_price_difference_categ'),False)
						income = context.get(('property_account_income_categ'),False)
						expense = context.get(('property_account_expense_categ'),False)
						input_category = context.get(('property_stock_account_input_categ'),False)
						output_category = context.get(('property_stock_account_output_categ'),False)
						valuation = context.get(('property_stock_valuation_account_id'),False)

                                                res={}
                                                
                                                if creditor:
                                                    res['property_account_creditor_price_difference_categ']=creditor
                                                if income:
                                                    res['property_account_income_categ']=expense
                                                if expense:
                                                    res['property_account_expense_categ']=expense
                                                if input_category:
                                                    res['property_stock_account_input_categ']=input_category
                                                if output_category:
                                                    res['property_stock_account_output_categ']=output_category
                                                if valuation:
                                                    res['property_stock_valuation_account_id']=valuation

						category.write(res)
