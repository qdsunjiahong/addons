#coding:utf-8

from openerp import models,fields

class zm_mrp(models.Model):
		_inherit='mrp.bom'

		unit_price = fields.Float(related='product_tmpl_id.standard_price',string="Cost Price",readonly=True)
		list_price = fields.Float(related="product_tmpl_id.list_price",string="List Price",readonly=True)

