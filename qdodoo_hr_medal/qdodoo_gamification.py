#! /usr/bin/env python
# -*- encoding:utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################


# from openerp import models, fields
from openerp.osv import osv, fields
from openerp.tools.translate import _


class qdodoo_gamification(osv.Model):
    _inherit = 'gamification.badge.user.wizard'
    _columns = {

        'employee_ids': fields.many2many('hr.employee', 'qdodoo_hr_employee_game', 'gamification_id',
                                         'employee_id',ondelete='cascade',
                                         string=u'员工'),
        'employee_id': fields.many2one("hr.employee", string='Employee'),
        # 'user_id': fields.related("employee_ids", "user_id",
        #                           type="many2one", relation="res.users",
        #                           store=True, string='User')
    }

    def action_grant_badge(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        badge_user_obj = self.pool.get('gamification.badge.user')
        grant_badge_obj = self.browse(cr, uid, ids[0], context=context)

        for line in grant_badge_obj.employee_ids:
            values = {
                'user_id': line.user_id.id,
                'sender_id': uid,
                'badge_id': grant_badge_obj.badge_id.id,
                'employee_id': line.id,
                'comment': grant_badge_obj.comment,
            }
            badge_user = badge_user_obj.create(cr, uid, values, context=context)
            result = badge_user_obj._send_badge(cr, uid, [badge_user], context=context)
        return result

    def action_grant_badge2(self, cr, uid, ids, context=None):
        """Wizard action for sending a badge to a chosen employee"""
        if context is None:
            context = {}


        badge_user_obj = self.pool.get('gamification.badge.user')

        for wiz in self.browse(cr, uid, ids, context=context):
            if not wiz.user_id:
                raise osv.except_osv(_('Warning!'), _('You can send badges only to employees linked to a user.'))

            if uid == wiz.user_id.id:
                raise osv.except_osv(_('Warning!'), _('You can not send a badge to yourself'))

            values = {
                'user_id': wiz.user_id.id,
                'sender_id': uid,
                'badge_id': wiz.badge_id.id,
                'employee_id': wiz.employee_id.id,
                'comment': wiz.comment,
            }

            badge_user = badge_user_obj.create(cr, uid, values, context=context)
            result = badge_user_obj._send_badge(cr, uid, [badge_user], context=context)
        return result



# class qdodoo_gamification_badge_use(osv.Model):
#     _inherit = 'gamification.badge.use'

