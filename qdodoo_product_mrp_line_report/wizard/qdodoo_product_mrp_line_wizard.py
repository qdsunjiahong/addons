# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api, _
import logging
from openerp.osv import osv

_logger = logging.getLogger(__name__)

class qdodoo_product_mrp_line_wizard(models.TransientModel):
    """
        报表查询条件模型
    """
    _name = 'qdodoo.product.mrp.line.wizard'

    company_id = fields.Many2one('res.company',u'公司', required=True)
    start_period = fields.Many2one('account.period',u'开始账期', required=True)
    end_period = fields.Many2one('account.period',u'结束账期', required=True)
    is_draft = fields.Boolean(u'勾选是否包含未标记')

    @api.multi
    def btn_search_date(self):
        # 完成判断条件
        domain = [('company_id','=',self.company_id.id)]
        if not self.is_draft:
            domain.append(('move_id.state','=','posted'))
        # 获取所有时间段内的账期
        period_obj = self.env['account.period'].search([('company_id','=',self.company_id.id),('date_start','>=',self.start_period.date_start),('date_stop','<=',self.end_period.date_stop)])
        if period_obj:
            domain.append(('period_id','in',period_obj.ids))
        # 获取查询的科目
        account_name = self.env['ir.config_parameter'].get_param('qdodoo.account')
        if not account_name:
            raise osv.except_osv(_(u'警告'),_(u'缺少需要的系统参数qdodoo.account！'))
        else:
            account_lst = account_name.strip(',').split(',')
        account_id = self.env['account.account'].search([('company_id','=',self.company_id.id),('name','in',account_lst)])
        if account_id:
            domain.append(('account_id','in',account_id.ids))
        else:
            raise osv.except_osv(_(u'警告'),_(u'该公司缺少对应的科目！'))
        # 查询出来所有满足条件的分录明细
        # 组织数据字典{产品：{总数量，总金额}}
        all_dict = {}
        for line in self.env['account.move.line'].search(domain):
            if not line.product_id:
                key = '其他'
            else:
                key = line.product_id
            # 如果贷方大于0,统计产量
            if line.credit:
                if key in all_dict:
                    all_dict[key]['number'] = all_dict[key].get('number',0) + line.quantity
                else:
                    all_dict[key] = {'number':line.quantity}
            # 如果借方金额大于0,统计金额
            if line.debit:
                if key in all_dict:
                    all_dict[key]['money'] = all_dict[key].get('money',0) + line.debit
                else:
                    all_dict[key] = {'money':line.debit}
        # 创建对应的报表数据
        # 收集创建数据的id
        ids_lst = []
        for key,value in all_dict.items():
            if key == '其他':
                name = '其他'
                price_unit = 0
            else:
                name = key.name
                price_unit = key.list_price
            sql = """insert into qdodoo_product_mrp_line_report (name,qty,price_unit,month_money) VALUES ('%s',%s,%s,%s) returning id"""%(
                name,value.get('number',0),price_unit,value.get('money',0)
            )
            self._cr.execute(sql)
            return_obj = self.env.cr.fetchall()
            if return_obj:
                ids_lst.append(return_obj[0][0])
        result = self.env['ir.model.data'].get_object_reference('qdodoo_product_mrp_line_report', 'view_tree_qdodoo_product_mrp_line_report')
        view_id = result and result[1] or False
        return {
              'name': ('产量成本明细表'),
              'view_type': 'form',
              "view_mode": 'tree',
              'res_model': 'qdodoo.product.mrp.line.report',
              'type': 'ir.actions.act_window',
              'domain': [('id','in',ids_lst)],
              'views': [(view_id,'tree')],
              'view_id': [view_id],
              }