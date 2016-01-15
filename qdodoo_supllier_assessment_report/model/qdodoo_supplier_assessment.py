# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class qdodoo_supplier_assessment_report(models.Model):
    _name = 'qdodoo.supplier.assessment.report'
    _description = 'qdodoo.supplier.assessment.report'

    ####title#######
    partner_name = fields.Many2one('res.partner', string=u'供应商')
    date_assessment = fields.Date(string=u'考核时间')
    supply_times = fields.Integer(string=u'供货次数')
    company_id = fields.Many2one('res.company', string=u'公司')
    supply_amount = fields.Float(string=u'供货金额')
    supply_supply_quantity = fields.Float(string=u'供货数量')
    supply_price = fields.Float(string=u'供货均价')
    category_staff = fields.Char(string=u'品类人员')
    order_personnel = fields.Char(string=u'订单人员')
    ####供应商质量考核########
    return_times = fields.Integer(string=u'退货次数')
    return_lines = fields.One2many('qdodoo.return.line', 'report_id', string=u'退货明细')
    # this_points = fields.Integer(string=u'此项扣分', compute='_get_this_points', multi='supplier_assessment')
    # system_evaluation = fields.Char(string=u'系统评价', compute='_get_this_points', multi='supplier_assessment')
    this_points = fields.Integer(string=u'此项扣分')
    system_evaluation = fields.Char(string=u'系统评价')
    #####供应商准交考核#####
    late_delivery_times = fields.Integer(string=u'迟交次数')
    late_delivery_lines = fields.One2many('qdodoo.late.delivery.line', 'report_id', string=u'迟交明细')
    this_points2 = fields.Integer(string=u'此项扣分')
    system_evaluation2 = fields.Char(string=u'系统评价')
    ######其他方面#########
    other_lines = fields.One2many('qdodoo.other.lines', 'report_id', string=u'明细')
    points = fields.Integer(string=u'此项扣分')
    #####系统考评#######
    final_score = fields.Integer(string=u'得分')
    grade = fields.Char(string=u'等级')
    ######供应商反馈#####
    supplier_feedback = fields.Text(string=u'供应商反馈')

    @api.one
    def _get_this_points(self):
        this_points = 0
        if self.return_times:
            this_points += self.return_times * -10
            self.this_points = this_points

    # @api.onchange('partner_name')
    def onchange_partner(self, cr, uid, ids, partner_name, context=None):
        res = {}
        if partner_name:
            report_id = ids
            partner_id = partner_name
            # 获取完成的采购单
            purchase_obj = self.pool.get('purchase.order')
            purchase_ids = purchase_obj.search(cr, uid, [('state', '=', 'done'), ('partner_id', '=', partner_id)])
            #########基本信息########
            date_assessment = fields.Date.today()
            supply_times = len(purchase_ids)  # 供货次数
            company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id  # 公司
            supply_amount = 0  # 供货金额
            supply_supply_quantity = 0  # 供货数量
            for purchase_id in purchase_obj.browse(cr, uid, purchase_ids):
                for invoice_id in purchase_id.invoice_ids:
                    for line in invoice_id.invoice_line:
                        supply_amount += line.quantity * line.price_unit
                        supply_supply_quantity += line.quantity
            ###供应商准交考核######
            delivery_list = []
            late_delivery_times = 0
            for po in purchase_obj.browse(cr, uid, purchase_ids):
                deal_date = po.deal_date
                for picking in po.picking_ids:
                    if picking.date_done > deal_date:
                        delivery_data = {
                            'late_order_name': po.name,
                            'order_date': deal_date,
                            'warehousing_date': picking.date_done,
                            'report_id': report_id
                        }
                        delivery_list.append(delivery_data)
                        late_delivery_times += 1

            invoice_obj = self.pool.get('account.invoice')
            ####供应商质量考核######
            # 已完成的供应商红字发票
            invoice_ids_return = invoice_obj.search(cr, uid,
                                                    [('partner_id', '=', partner_id), ('type', '=', 'in_refund'),
                                                     ('state', '=', 'paid')])
            return_times = len(invoice_ids_return)  # 退货次数
            stock_picking_obj = self.pool.get('stock.picking')
            return_list = []
            for invoice_id_return in invoice_obj.browse(cr, uid, invoice_ids_return):
                origin = invoice_id_return.origin
                origin_list = origin.split(":")
                return_order = origin_list[0]
                picking_ids = stock_picking_obj.search(cr, uid, [('name', '=', return_order), ('state', '=', 'done')])
                return_date = stock_picking_obj.browse(cr, uid, picking_ids[0]).date_done
                return_amount = invoice_id_return.amount_total
                return_line = {'return_order': return_order, 'return_date': return_date, 'return_amount': return_amount,
                               'report_id': report_id}
                return_list.append(return_line)
            if supply_supply_quantity == 0:
                supply_price = 0
            else:
                supply_price = supply_amount / supply_supply_quantity
            res['value'] = {'supply_amount': supply_amount, 'supply_supply_quantity': supply_supply_quantity,
                            'date_assessment': date_assessment,
                            'supply_times': supply_times, 'company_id': company_id,
                            'supply_price': supply_price,
                            'return_lines': return_list, 'late_delivery_lines': delivery_list,
                            'return_times': return_times, 'late_delivery_times': late_delivery_times}
            return res


class qdodoo_return_line(models.Model):
    _name = 'qdodoo.return.line'
    _description = 'qdodoo.return.line'
    return_order = fields.Char(string=u'退货单号')
    return_date = fields.Char(string=u'退货时间')
    return_amount = fields.Char(string=u"退货金额")
    report_id = fields.Many2one('qdodoo.supplier.assessment.report')


class qdodoo_late_delivery_line(models.Model):
    _name = 'qdodoo.late.delivery.line'
    _description = 'qdodoo.late.delivery.line'

    late_order_name = fields.Char(string=u'迟交单号')
    order_date = fields.Date(string=u'订单日期')
    warehousing_date = fields.Date(string=u'入库日期')
    report_id = fields.Many2one('qdodoo.supplier.assessment.report')


class qdodoo_other_lines(models.Model):
    _name = 'qdodoo.other.lines'
    _description = 'qdodoo.other.lines'
    evaluation_items = fields.Char(string=u'评价项')
    text = fields.Text(string=u'备注')
    points = fields.Selection([('0', 0), ('5', 5), ('10', 10), ('15', 15), ('20', 20)], string=u'扣分')
    report_id = fields.Many2one('qdodoo.supplier.assessment.report')
