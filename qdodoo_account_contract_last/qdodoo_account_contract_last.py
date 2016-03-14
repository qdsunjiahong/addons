#-*- coding:utf-8 -*-

from openerp import models,fields,_,api
import logging
_logger = logging.getLogger(__name__)

class qdodoo_account_contract_last(models.TransientModel):
    """
    最近供货商状态列表模块
    models.TransientModel表示会被定期清理数据的模块
    """
    _name = 'qdodoo.account.contract.last'
    _description = u"最近合同状态列表"

    ctype = fields.Many2one('contract.type', string=u'合同类型', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'供货商名称', readonly=True)
    company_id = fields.Many2one('res.company', string=u'合同公司', readonly=True)
    order_manger_id = fields.Many2one('res.users', string=u'签署人', readonly=True)
    cstate = fields.Char(string=u'合同状态')
    state = fields.Selection([('template', u'模版'),('draft',u'新建'), ('open',u'进行中'), ('pending',u'要续签的'), ('close',u'已关闭'), ('cancelled', u'已取消')], u'合同状态',)


    def action_search_last_contact(self, cr, uid, ids, context=None):
        """
        按条件查询合同数据并赋值，然后调用视图显示结果
        """

        #先清除旧的数据
        old_ids = self.search(cr, uid, [])
        self.unlink(cr, uid, old_ids)

        #查找合同
        repeat_dict = {}
        show_ids = []

        contract_obj = self.pool['account.analytic.account']
        contract_ids = contract_obj.search(cr, uid, [], order='date_start desc')
        for contract in contract_obj.browse(cr, uid, contract_ids):
            #获取要显示的数据
            contract_type = contract.contract_type1
            partner_id = contract.partner_id.id
            company_id = contract.company_id.id
            omanager_id = contract.order_manager_id.id
            contract_state = contract.contract_state
            state = contract.state  #这个state在此处不需要

            #重复键：由公司ID+供货商ID组成，避免重复同一供货商和同一公司签的合同
            repeat_key = str(company_id)+','+str(partner_id)

            if repeat_key not in repeat_dict:
                repeat_dict[repeat_key] = True  #存入重复键

                #创建记录
                create_id = super(qdodoo_account_contract_last, self).create(cr, uid, {
                    'ctype': contract_type.id,
                    'partner_id': partner_id,
                    'company_id': company_id,
                    'order_manger_id': omanager_id,
                    'cstate': contract_state,
                    'state': state,
                })


            show_ids.append(create_id)

        #查找视图，负载查找到的数据显示
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_account_contract_last', 'tree_last_contract')
        view_id = result and result[1] or False
        return {
              'name': u'当前合同状态',
              'view_type': 'form',
              "view_mode": 'tree',
              'res_model': 'qdodoo.account.contract.last',
              'type': 'ir.actions.act_window',
              'domain': [('id', 'in', show_ids)],
              'view_id': [view_id],
              }
