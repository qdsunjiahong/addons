# -*- encoding:utf-8 -*-

from openerp import models, fields, api, _
# from openerp import models,fields

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    finished_goods = fields.Many2one('product.product',string=u'成品名称', compute='_get_finished_goods')

    @api.one
    def _get_finished_goods(self):
        if self.name:
            print "self.name=",self.name
            try:
                mrp_product_list = self.env['mrp.production'].search([('name', '=', self.name)])
                # print "mrp_product_list", mrp_product_list
                # print 'mrp_product_list[0].product_id.id', mrp_product_list[0].partner_id
                if len(mrp_product_list):
                    self.finished_goods = mrp_product_list[0].product_id
            except:
                pass


