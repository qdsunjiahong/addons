#coding:utf-8

from openerp import models,fields,api,_

class zm_mrp_line(models.Model):
		_inherit='mrp.bom.line'
		
		cost_price = fields.Float(string='Cost Price',related='product_id.standard_price')

		category = fields.Selection(stirng="category",selection=[('main',u'主料'),('accesssory',u'辅料')])

		cost_amount = fields.Float(compute='_get_cost_amount',string="Cost Amount")	

		@api.one
		def _get_cost_amount(self):
				self.cost_amount = self.cost_price * self.product_qty / self.product_efficiency

