# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields


class qdodoo_contract_expire_report(models.Model):
    _name = 'qdodoo.contract.expire.report'
    _description = 'qdodoo.contract.expire.report'
    _order = 'date_end'

    contract_name = fields.Char(string=u'合同名称')
    partner_id = fields.Many2one('res.partner', string=u'供应商')
    contract_company = fields.Many2one('contract.company', string=u'合同公司')
    contract_type = fields.Many2one('contract.type', string=u'合同类型')
    manager_id = fields.Many2one('res.users', string=u'科目管理员')
    date_end = fields.Date(string=u'过期日期')
    contract_state = fields.Selection(((u'正常', u'正常'), (u'到期', u'到期'), (u'即将到期', u'即将到期')), string=u'合同状态')
