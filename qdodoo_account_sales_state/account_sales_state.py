# -*- coding: utf-8 -*-
###########################################################################################
#
#    account.sales.state for Odoo8.0
#    Copyright (C) 2016 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import tools
import openerp.addons.decimal_precision as dp
from openerp import models, fields, api, _
from openerp.exceptions import except_orm

class account_sales_state_search(models.Model):
    """
    用于弹出搜索并执行的model
    """
    _name = 'account.sales.state.search'
    _description = u'查找消费明细'

    def start_date(self):
        """
        默认今天
        """
        now_date = fields.Date.today()
        return now_date

    company_id = fields.Many2one('res.company', string=u'公司', required=True)
    start_period_id = fields.Many2one('account.period', string=u'会计开始期间', required=True)
    end_period_id = fields.Many2one('account.period', string=u'会计结束期间', required=True)
    cstate = fields.Boolean(u'包含未记账')

    @api.multi
    def sales_state_search_open(self):
        """
        根据查询条件查询数据，填写account.sales.state.result模型，再调用视图显示
        """
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        account_account_obj = self.env['account.account']
        state_obj = self.env["qdodoo.account.sales.state.result"]

        #参数
        sale_account_list = self.env['ir.config_parameter'].get_param('qdodoo.account.sales.sate.account1').replace(u'，', ',').split(',')
        cost_account_list = self.env['ir.config_parameter'].get_param('qdodoo.account.sales.sate.account2').replace(u'，', ',').split(',')

        #整理各查询条件
        domain = [('company_id', '=', self.company_id.id)]

        #计算设置的会计区间的所有会计期间
        if self.start_period_id.date_start >= self.end_period_id.date_stop:
            raise except_orm(_(u'时间错误'), _(u'选择的结束时间不得大于开始时间！'))
        else:
            period_ids = self.env['account.period'].search([('date_start', '>=', self.start_period_id.date_start), ('date_stop', '<=', self.end_period_id.date_stop), ('company_id', '=', self.company_id.id)])
            domain.append(('period_id', 'in', period_ids.ids))

        #是否包含未记账，如果未勾选，则只查找已登帐的
        if not self.cstate:
            domain.append(('state', '=', 'posted'))

        #从会计凭证查询数据：根据公司、会计期间、是否登帐条件查询
        id2account_move_state_dict = {}
        account_move_ids = account_move_obj.search(domain)

        #限制科目为“主营业务收入”、“其他业务收入”和“主营业务成本”等类型
        id2account_name_dict = {}  #科目ID->科目名称，便于后面按科目类型计算销量/成本
        account_account_ids = account_account_obj.search([('name', 'in', sale_account_list+cost_account_list)])
        for account_account in account_account_ids:
            id2account_name_dict[account_account.id] = account_account.name

        """
        根据之前查询的会计凭证和会计科目限制下，查询会计分录明细
        查询其中的商品ID，数量，借方，贷方
        以商品ID为key建立字典，相当于按商品分组
        {pid:{quantity:销量, price:销售价格, sales：销售收入, cost:销售成本}, pid2:{...}...}
        """
        pid2pinfo_dic = {}
        account_move_line_ids = account_move_line_obj.search([('move_id', 'in', account_move_ids.ids), ('account_id', 'in', account_account_ids.ids), ('company_id', '=', self.company_id.id)])
        for account_move_line in account_move_line_ids:
            product_id = account_move_line.product_id.id  #商品ID
            account_name = id2account_name_dict[account_move_line.account_id.id]  #所属会计科目名称
            quantity_float = account_move_line.quantity  #数量
            debit_float = account_move_line.debit  #借方金额
            credit_float = account_move_line.credit  #贷方金额

            if not product_id in pid2pinfo_dic:
                #初始化该商品字典
                pid2pinfo_dic[product_id] = {
                    'quantity': 0,   #销量
                    'price': 0,  #销售价格
                    'sales': 0,  #销售收入
                    'cost': 0,  #销售成本
                }

            if account_name in sale_account_list:
                #主营业务收入 和 其他业务收入 数量累加入销量，贷方金额累加入销售收入
                if credit_float>0:
                    pid2pinfo_dic[product_id]['quantity'] += quantity_float

                pid2pinfo_dic[product_id]['sales'] += credit_float
            else:
                #主营业务成本的借方金额累加入销售成本
                pid2pinfo_dic[product_id]['cost'] += debit_float

        #循环计算产品的销售价格 = 销售收入/销量，并存储模型数据
        insert_ids_list = []
        for product_id, product_info_dict in pid2pinfo_dic.items():
            if product_info_dict['quantity']==0:
                product_price = 0
            else:
                product_price = pid2pinfo_dic[product_id]['price'] = product_info_dict['sales'] / product_info_dict['quantity']

            create_param_dict = {
                'product_id': product_id,
                'sale_quantity': product_info_dict.get('quantity', 0),
                'sale_price': product_price,
                'sale_earning': product_info_dict.get('sales', 0),
                'sale_cost': product_info_dict.get('cost', 0),

                #以下帐期ID，科目ID，公司ID主要用于测试查看
                'period_id':product_info_dict.get('period_id', 0),
                'account_id': product_info_dict.get('account_id', 0),
                'company_id': product_info_dict.get('company_id', 0),
                'cstate': product_info_dict.get('state', ''),
            }

            create_obj = state_obj.create(create_param_dict)
            insert_ids_list.append(create_obj.id)

        view_model, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_account_sales_state',
                                                               'view_result_sales_state_tree')
        return {
            'name': u'销售明细报表',
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'qdodoo.account.sales.state.result',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', insert_ids_list)],
            'views': [(view_id, 'tree')],
            'view_id': [view_id],
        }

class qdodoo_account_sales_state_result(models.TransientModel):
    _name = "qdodoo.account.sales.state.result"
    _description = u"销售明细表"
    _rec_name = 'sale_quantity'
    _order = 'product_id desc'

    product_id = fields.Many2one('product.product', string=u'产品名称', readonly=True)
    account_id = fields.Many2one('account.account', string=u'会计科目', readonly=True)
    sale_quantity = fields.Float(string=u'销量', digits=(20,4), readonly=True)
    sale_price = fields.Float(string=u'销售单价', digits=(20,4), readonly=True)
    sale_earning = fields.Float(string=u'销售收入', digits=(20,4), readonly=True)
    sale_cost = fields.Float(string=u'销售成本', digits=(20,4), readonly=True)
    period_id = fields.Many2one('account.period', string=u'会计期间', readonly=True)
    company_id = fields.Many2one('res.company', string=u'公司', readonly=True)
    cstate = fields.Selection([('draft',u'未登帐'), ('posted',u'已登帐')], string=u'状态', readonly=True)





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
