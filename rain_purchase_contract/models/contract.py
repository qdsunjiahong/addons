# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import except_orm
from datetime import datetime

class rain_contract(models.Model):
    _inherit="account.analytic.account"

    contract_type1 = fields.Many2one('contract.type','Contract_type1',required=True)
    contract_company1 = fields.Many2one('contract.company','Contract_company1',required=True)
    contract_state = fields.Selection([('ok',u'正常'),('no',u'到期'),('date',u'即将到期')],u'合同状态',required=True)
    contract_partner_no = fields.Char('Contract_partner_no')#,required=True
    contract_company_no = fields.Char('Contract_company_no')#,required=True
    partner_id = fields.Many2one('res.partner','partner_id',required=True)
    contract_no = fields.Char('contract_no',required=True)
    @api.onchange('partner_id')
    def on_change_partner_id(self):
        self.contract_partner_no = self.partner_id.ref
        if not self.partner_id.ref:
            self.contract_partner_no = 0
        self._get_no()
    @api.onchange('contract_company1')
    def _onchange_contract_company(self):
        self.contract_company_no = self.contract_company1.contract_company_no
        if not self.partner_id.ref:
            self.contract_partner_no = 0       
        self._get_no()
    @api.one
    def _get_no(self):
        if not self.contract_partner_no :
            self.contract_partner_no = 0
        elif not self.contract_company_no : self.contract_company_no = 0
        elif not self.code : self.code = 0
        self.contract_no = self.contract_partner_no + self.contract_company_no + self.code

    def get_contract_state(self, cr, uid):
        ids = self.search(cr, uid, [])
        ids_lst = {}
        for obj in self.browse(cr, uid, ids):
            if obj.date:
                period = datetime.strptime(obj.date, '%Y-%m-%d') - datetime.now()
                days = period.days
            else:
                days = 50
            if days < 0 and obj.contract_state != 'no':
                ids_lst[obj.id] = 'no'
            if 0 < days < 15 and obj.contract_state != 'date':
                ids_lst[obj.id] = 'date'
            if days >15 and obj.contract_state != 'ok':
                ids_lst[obj.id] = 'ok'
        for key,value in ids_lst.items():
            super(rain_contract, self).write(cr, uid, key, {'contract_state':value})

class rain_contract_type(models.Model):
    _name="contract.type"
    contract_type_no = fields.Integer('Contract_type_no')
    name = fields.Char('Contract_type_name',required=True)
class rains_contract_company(models.Model):
    _name="contract.company"
    contract_company_no = fields.Integer('Contract_company_no')
    name = fields.Char('Contract_company_name',required=True)
