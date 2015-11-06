# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_contract_expire_search(models.Model):
    """
    到期合同查询wizard
    """
    _name = 'qdodoo.contract.expire.search'
    _description = 'qdodoo.contract.expire.search'

    start_date = fields.Date(string=u'开始时间', required=True)
    end_date = fields.Date(string=u'结束时间')

    @api.multi
    def action_search(self):
        end_date_new = fields.Date.today()
        if self.end_date:
            end_date_new = self.end_date
        contract_ids = self.env['account.analytic.account'].search(
            [('date', '>=', self.start_date), ('date', '<=', end_date_new),
             ('contract_state', '=', u'到期')])
        return_list = []
        if contract_ids:
            for contract_id in contract_ids:
                data = {
                    'contract_name': contract_id.name,
                    'partner_id': contract_id.partner_id.id,
                    'contract_company': contract_id.contract_company1.id,
                    'contract_type': contract_id.contract_type1.id,
                    'manager_id': contract_id.manager_id.id,
                    'date_end': contract_id.date,
                    'contract_state': contract_id.contract_state
                }
                cre_obj = self.env['qdodoo.contract.expire.report'].create(data)
                return_list.append(cre_obj.id)
            view_mod, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_contract_expire_search',
                                                                               'qdodoo_contract_expire_report_tree')
            return {
                'name': _('合同状态报表'),
                'view_type': 'form',
                "view_mode": 'tree',
                'res_model': 'qdodoo.contract.expire.report',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', return_list)],
                'views': [(view_id, 'tree')],
                'view_id': [view_id],
            }
