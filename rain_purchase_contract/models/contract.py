# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import except_orm

class rain_contract(models.Model):
    _inherit="account.analytic.account"

	#contract_no = fields.Char('Contract_no',required=True)
    #contract_name = fields.Char('Contract_name',required=True)
    #contract_date = fields.Date('Contract_date',required=True)
    #contract_type = fields.Selection((('a',u'临时合同'),('b',u'长期合同')),'Contract_type',required=True)
    #contract_company = fields.Selection((('a',u'香界'),('b',u'惠美')),'Contract_company',required=True)
    contract_type1 = fields.Many2one('contract.type','Contract_type1',required=True)
    contract_company1 = fields.Many2one('contract.company','Contract_company1',required=True)
    contract_state = fields.Selection(((u'正常',u'正常'),(u'到期',u'到期'),(u'即将到期',u'即将到期')),u'合同状态',required=True)
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

class rain_contract_type(models.Model):
    _name="contract.type"
    contract_type_no = fields.Integer('Contract_type_no')
    name = fields.Char('Contract_type_name',required=True)
class rains_contract_company(models.Model):
    _name="contract.company"
    contract_company_no = fields.Integer('Contract_company_no')
    name = fields.Char('Contract_company_name',required=True)
