# -*- coding: utf-8 -*-
###########################################################################################
#
# module name for OpenERP
# Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import osv, fields
from datetime import datetime


class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'  # 继承

    def _get_days(self, cr, uid, ids, field, arg, context=None):
        result = {}

        for line in self.browse(cr, uid, ids, context=context):
            if line.date:
                period = datetime.strptime(line.date, '%Y-%m-%d') - datetime.now()
                days = period.days
                if days > 45:
                    line.write({'contract_state': u'正常'})
                elif days <= 45 and days > 15:
                    line.write({'contract_state': u'即将到期'})
                elif days <= 15 and days >= 0:
                    line.write({'contract_state': u'即将到期'})
                else:
                    line.write({'contract_state': u'到期'})
                result[line.id] = int(days)
            else:
                line.write({'contract_state': u'正常'})
                result[line.id] = 50
        return result



    _columns = {  # 定义字段
                  'sms_one_ok': fields.boolean(u'第一次提醒'),
                  'sms_two_ok': fields.boolean(u'第二次提醒'),
                  'erp_ok': fields.boolean(u'管理员提醒'),
                  'days': fields.function(_get_days, type='integer', string=u'离到期日天数'),
                  # 'color': fields.function(_get_color, type='char', string=u'颜色'),
                  'erp_manager_ids': fields.many2many('res.users', 'erp_manager_users', 'user_id', 'manager_id',
                                                      string=u'erp信息管理员')
                  }
