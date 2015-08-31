# -*- coding: utf-8 -*-


from openerp.osv import fields, osv

class rain_cost_share_settings(osv.osv_memory):
    _name = 'rain.cost.share.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'rain_account_journal' : fields.many2one('account.journal',u'成本分摊记录的账簿'),
        'rain_account_left' : fields.many2one('account.account', u'记入账簿的科目1(分摊的成本差异)'),
        'rain_account_right': fields.many2one('account.account',u'记入账簿的科目2(主要业务成本)')
    }
