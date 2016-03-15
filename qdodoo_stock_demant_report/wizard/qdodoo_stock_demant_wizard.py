# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_stock_demant_wizard(models.Model):
    """
    内部调拨转移差异报表查询wizard
    """
    _name = 'qdodoo.stock.demant.wizard'
    _description = 'qdodoo.stock.demant.wizard'

    def _get_start_date(self):
        today = fields.Date.today()
        return today[:8] + "01"

    def _get_company_id(self):
        return self.env['res.users'].browse(self.env.uid).company_id.id

    start_date = fields.Date(string=u'开始时间', required=True, default=_get_start_date)
    end_date = fields.Date(string=u'结束时间')
    company_id = fields.Many2one('res.company', string=u"公司", default=_get_company_id)

    @api.multi
    def action_search(self):
        report_obj = self.env['qdodoo.stock.demant.report']
        # report_ids = report_obj.search([])
        # report_ids.unlink()
        sql_select = "delete from qdodoo_stock_demant_report where 1=1"
        self.env.cr.execute(sql_select)
        # 查询当前登录人允许查看的公司company_ids
        sql_company = """
            select rcul.cid as com_id
            from res_company_users_rel rcul
            WHERE rcul.user_id=%s
            GROUP BY rcul.cid,rcul.user_id
        """ % self.env.uid
        company_ids = []
        com_result = self.env.cr.execute(sql_company)
        if com_result:
            for com in com_result:
                company_ids.append(com[0])
        company_ids.append(self.company_id.id)
        company_ids_new = list(set(company_ids))
        # 过滤时间
        if self.end_date:
            if self.start_date > self.end_date:
                raise except_orm(_(u'警告'), _(u'开始时间不能大于结束时间'))
            # 查询时间段内完成的需求转换单
            sd_ids = self.env['qdodoo.stock.demand'].search(
                [('date_planed', '<=', self.end_date), ('company_id', 'in', company_ids_new),
                 ('date_planed', '>=', self.start_date), ('state', '=', 'done')])
        else:
            sd_ids = self.env['qdodoo.stock.demand'].search(
                [('company_id', 'in', company_ids_new),
                 ('date_planed', '>=', self.start_date), ('state', '=', 'done')])
        result_list = []
        # 查询出来的需求转换单
        if sd_ids:
            out_num_dict = {}  # 出库数量
            location_s_id_dict = {}  # 源库位
            location_d_id_dict = {}  # 目的库位
            in_num_dict = {} #入库数量
            for si_id in sd_ids:
                sd_list = []  # 需求单列表
                location_d_id = si_id.location_id2.id  # 目的库位id
                # 根据需求转换单id查询对应的录像
                sql = """
                    select route_id
                    from stock_location_route_demand
                    WHERE procurement_id = %s
                    GROUP BY route_id
                """ % si_id.id
                self.env.cr.execute(sql)
                sql_result = self.env.cr.fetchall()
                if sql_result:
                    # 获取路线模型
                    ruoute_obj = self.env['stock.location.route'].browse(sql_result[0][0])
                    location_s_id = False
                    # 获取路线的源库位对象
                    for i in ruoute_obj.pull_ids:
                        if i.picking_type_id.code == 'outgoing':
                            location_s_id = i.location_src_id.id  # 源库位对象
                    # 获取需求转换单对应的需求单
                    procurement_ids = self.env['procurement.order'].search([('order_id_new','=',si_id.id)])
                    for line_id in procurement_ids:
                        sd_list.append(line_id.id)
                    # 查询调拨单
                    stock_picking_out_ids = self.env['stock.move'].search(
                        [('procurement_id', 'in', sd_list), ('state', '=', 'done')])
                    for pick_id in stock_picking_out_ids:
                        if pick_id.location_id.id == location_s_id:
                            out_num_dict[si_id.id] = out_num_dict.get(si_id.id, 0) + pick_id.product_uom_qty
                        elif pick_id.location_dest_id.id == location_d_id:
                            in_num_dict[si_id.id] = in_num_dict.get(si_id.id, 0) + pick_id.product_uom_qty
                    location_s_id_dict[si_id.id] = location_s_id
                    location_d_id_dict[si_id.id] = location_d_id
                    data = {
                        'sd_id':si_id.id,
                        'location_id':location_s_id,
                        'qty_out': out_num_dict.get(si_id.id, 0),
                        'location_dest_id': location_d_id,
                        'qty_in': in_num_dict.get(si_id.id, 0),
                        'dif': out_num_dict.get(si_id.id, 0) - in_num_dict.get(si_id.id, 0),
                        'company_id': self.company_id.id
                    }
                    if (out_num_dict.get(si_id.id, 0) - in_num_dict.get(si_id.id, 0)) != 0:
                        cre_obj = report_obj.create(data)
                        result_list.append(cre_obj.id)
        view_mod, view_id = self.env['ir.model.data'].get_object_reference('qdodoo_stock_demant_report',
                                                                               'qdodoo_stock_demand_report_tree')
        return {
            'name': _('内部调拨转移差'),
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'qdodoo.stock.demant.report',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', result_list)],
            'views': [(view_id, 'tree')],
            'view_id': [view_id],
        }
