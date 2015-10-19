# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class qdodoo_contract_report(models.Model):
    _name = 'qdodoo.contract.report'

    contract_type = fields.Many2one('contract.type', string=u'合同类型')
    partner_id = fields.Many2one('res.partner', string=u'供应商名称')
    number = fields.Integer(string=u'数量')
    contract_state = fields.Selection([('expire', u'过期'), ('void', u'作废'), ('open', u'正常')],
                                      string=u'合同状态')
    contract_company = fields.Many2one('contract.company', string=u'合同公司')
    manager_id = fields.Many2one('res.users', string=u'签署人')


class qdodoo_search_contract(models.Model):
    _name = 'qdodoo.search.contract'

    date_start = fields.Date(string=u'开始时间')
    date_end = fields.Date(string=u'结束时间')

    def state_return(self, contract_obj, context=None):
        number_days = datetime.now() - datetime.strptime(contract_obj.create_date, DEFAULT_SERVER_DATETIME_FORMAT)
        state_c = {'state': ''}
        # if number_days.days < 15:
        # state_c['state'] = 'new'
        if fields.Date.today() > contract_obj.date:
            state_c['state'] = 'expire'
        else:
            state_c['state'] = 'open'
        if contract_obj.state in ('cancelled', 'close'):
            state_c['state'] = 'void'

        return state_c

    @api.multi
    def action_done(self):
        if self.date_start > self.date_end:
            raise except_orm(_(u'警告'), _(u'开始时间不能大于结束时间'))
        id_list = []
        type_list = []
        contract_dict = {}
        user_dict = {}
        company_dict = {}
        if self.date_start and not self.date_end:
            date_start_new = str(self.date_start) + " 00:00:01"
            contract_ids = self.env['account.analytic.account'].search([('create_date', '>', date_start_new)])
        elif not self.date_start and self.date_end:
            date_end_new = str(self.date_end) + " 23:59:59"
            contract_ids = self.env['account.analytic.account'].search([('create_date', '<', date_end_new)])
        elif self.date_start and self.date_end:
            date_start_new = str(self.date_start) + " 00:00:01"
            date_end_new = str(self.date_end) + " 23:59:59"
            contract_ids = self.env['account.analytic.account'].search(
                [('create_date', '>', date_start_new), ('create_date', '<', date_end_new)])
        else:
            contract_ids = self.env['account.analytic.account'].search([])
        if contract_ids:
            for contract_id in contract_ids:
                state_contract = self.state_return(contract_id).get('state', '')
                if (contract_id.contract_type1.id, contract_id.partner_id.id, state_contract) in type_list:
                    contract_dict[
                        (contract_id.contract_type1.id, contract_id.partner_id.id, state_contract)] = contract_dict.get(
                        (contract_id.contract_type1.id, contract_id.partner_id.id, state_contract), 0) + 1
                else:
                    contract_dict[(contract_id.contract_type1.id, contract_id.partner_id.id, state_contract)] = 1
                    type_list.append((contract_id.contract_type1.id, contract_id.partner_id.id, state_contract))
                user_dict[
                    (contract_id.contract_type1.id, contract_id.partner_id.id,
                     state_contract)] = contract_id.manager_id.id
                company_dict[(contract_id.contract_type1.id, contract_id.partner_id.id,
                              state_contract)] = contract_id.contract_company1.id
        for line in type_list:
            data = {
                'contract_type': line[0],
                'partner_id': line[1],
                'number': contract_dict.get(line, 0),
                'contract_state': line[2],
                'contract_company': company_dict.get(line, False),
                'manager_id': user_dict.get(line, False),
            }
            id_obj = self.env['qdodoo.contract.report'].create(data)
            id_list.append(id_obj.id)
        vie_mod, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_contract_report_new',
                                                                          'qdodoo_contract_report_view_tree')
        return {
            'name': _('合同报表'),
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'qdodoo.contract.report',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', id_list)],
            'views': [(view_id, 'tree')],
            'view_id': [view_id],
        }
