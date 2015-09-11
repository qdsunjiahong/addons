# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Autor:Kevin Kong (kfx2007@163.com)
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

from openerp import fields,api,_,models

# class department_account(models.Model):
#     _name="product.expense.account"
#
#     name=fields.Char('Name',required=True)
#     department = fields.Many2one('hr.department','Department',required=True)
#     analytic_acc = fields.Many2one('account.analytic.account','Analytic Account')
#     #line_ids = fields.One2many('product.expense.account.line','account_id','Lines')
#     warehouse = fields.Many2one('stock.warehouse','Warehouse')
#     location = fields.Many2one('stock.location','Location',domain=[('usage','=','internal')])
#
#     @api.model
#     def create(self,vals):
# 		expense_loc = self.env['stock.location'].search([('name','=','Expense')])
# 		res =  super(department_account,self).create(vals)
# 		#create proper route for selected warehouse.
# 		# pull_obj = self.env['procurement.rule']
# 		# if not pull_obj.search([('location_id','=',expense_loc.id),('warehouse_id','=',res.warehouse.id)]):
# 		# 	pull_obj.create({'name':'Expense Route → '+res.warehouse.name,
# 		# 		'location_id':expense_loc.id,
# 		# 		'warehouse_id':res.warehouse.id,
# 		# 		'procure_method':'make_to_stock',
# 		# 		'action':'move',
# 		# 		'picking_type_id':res.warehouse.out_type_id.id,
# 		# 		'location_src_id':res.location.id,
# 		# 	})
# 		return res
#
#
#     @api.multi
#     def write(self,vals):
# 		expense_loc = self.env['stock.location'].search([('name','=','Expense')])
# 		warehouse = vals.get('warehouse') or False
# 		location = vals.get('location') or False
# 		if warehouse or location:
# 			route = self.env['procurement.rule'].search([('location_id','=',expense_loc.id),('warehouse_id','=',self.warehouse.id)])
# 			if route:
# 				if warehouse:
# 					route.write({'warehouse_id':warehouse})
# 				if location:
# 					route.write({'location_id':location})
# 		return super(department_account,self).write(vals)
#
#
# class department_account_line(models.Model):
#     _name='product.expense.account.line'
#
#     account_id = fields.Many2one('product.expense.account')
#     #product_category = fields.Many2one('product.category','Product Category')
#     name = fields.Char('Name')
#     in_account = fields.Many2one('account.account','Credit')
#     out_account = fields.Many2one('account.account','Debit')

class product_expense_usage(models.Model):
	_name='product.expense.usage'

	name= fields.Char('Name',required=True)
	credit = fields.Many2one('account.account','Credit',required=True)
	debit = fields.Many2one('account.account','Debit',required=True)
