# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:Qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, _, api, fields

class tms_res_partner(models.Model):
    """
        线路信息
    """
    _inherit = 'res.partner'

    tms_location_id = fields.Many2one('stock.warehouse',u'物流中心')
    portal_plus = fields.Float(u'单店加收费')
    warm_box = fields.Float(u'保温箱费用')
    tms_other = fields.Float(u'其他费用')
    tms_piece = fields.Float(u'件费用')
    return_warm_box = fields.Float(u'回箱费用')
    tms_line_id = fields.Many2one('tms.partner.line',u'线路')

class tms_partner_line(models.Model):
    """
        线路信息
    """
    _name = 'tms.partner.line'

    name = fields.Char(u'线路编码')

class tms_product_template(models.Model):
    """
        产品模板增加装箱数
    """
    _inherit = 'product.template'

    tms_box_num = fields.Integer(u'每箱数量')

class tms_stock_picking(models.Model):
    """
        调拨单增加箱数
    """
    _inherit = 'stock.picking'

    box_num = fields.Integer(u'箱数', compute='_get_box_num')

    def _get_box_num(self):
        for ids in self:
            num = 0.0
            for line in ids.move_lines:
                if line.product_id.tms_box_num:
                    num += line.product_uom_qty/line.product_id.tms_box_num
            new_num = int(num)
            if new_num < num:
                new_num += 1
            ids.box_num = new_num
