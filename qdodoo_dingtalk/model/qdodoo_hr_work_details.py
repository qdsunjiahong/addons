# -*- coding: utf-8 -*-
###########################################################################################
#
# module name for OpenERP
#    Copyright (C) 2016 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_work_details(models.Model):
    '''
    工作日志
    '''
    _name = 'qdodoo.work.details'
    _description = 'work datails'
    _rec_name = 'category_id'

    category_id = fields.Many2one('qdodoo.detail.category', string=u'日志主题')
    partner_ids = fields.Many2many('res.partner', 'work_details_res_partner', 'work_detail_id', 'partner_id',
                                   string=u'共享')
    c_date = fields.Datetime(string=u'创建日期')
    # end_date = fields.Datetime(string=u'结束日期')
    text = fields.Text(string=u'内容')
    user_id = fields.Many2one('res.users', string=u'创建者', default=lambda self: self.env.user)

    _defaults = {
        'c_date': fields.datetime.now(),
        # 'end_date': fields.datetime.now(),
        # 'user_id': lambda obj, cr, uid, context: uid,
    }


class qdodoo_detail_category(models.Model):
    """
    日志类型
    """
    _name = 'qdodoo.detail.category'
    _description = 'qdodoo.detail.category'

    name = fields.Char(string=u'日志类型', required=True)
