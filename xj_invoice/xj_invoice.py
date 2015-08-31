# coding:utf-8

from openerp import fields,api,_,models

class xj_invoice(models.Model):
	_inherit="account.move"

	ref_inv = fields.Many2one('account.move',string="Ref Inv",compute="_get_inv")

	@api.one
	def _get_inv(self):
			if self.journal_id.id==9:
					inv = self.env['account.invoice'].search([('origin','=',self.ref)])
                                        if len(inv)==1:
						self.ref_inv = inv.move_id
                                        elif len(inv)>1:
	                                        self.ref_inv = inv[0].move_id
