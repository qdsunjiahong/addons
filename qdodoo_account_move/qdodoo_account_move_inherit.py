# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.osv import osv


class qdodoo_account_move_tfs(models.Model):
    _name = 'qdodoo.account.move'

    # 批量过账凭证
    def btn_merge(self, cr, uid, ids, context=None):
        account_obj = self.pool.get('account.move')
        for line in account_obj.browse(cr, uid, context.get('active_ids')):
            if line.state != 'draft':
                raise osv.except_osv(_('警告!'),_('只能过账草稿状态的运费单.'))
        account_obj.button_validate(cr, uid, context.get('active_ids'))
        return True

