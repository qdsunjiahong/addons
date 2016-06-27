# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:Qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, _, api, fields
from openerp.osv import osv
from datetime import datetime

class tms_stowage(models.Model):
    """
        配载
    """
    _name = 'tms.stowage'

    name = fields.Char(u'配载单号')
    date = fields.Date(u'时间', default=lambda self:fields.date.today())
    car_id = fields.Many2one('tms.car.information',u'车辆')
    price = fields.Many2one('tms.car.information.price',u'基础费用')
    order_line = fields.One2many('tms.stowage.line','order_id',u'配载信息')
    state = fields.Selection([('draft',u'草稿'),('done',u'完成'),('cancel',u'取消')],u'状态',default='draft')
    all_money = fields.Float(u'总合计金额', compute='_get_all_money')
    report_line = fields.One2many('tms.stowage.report','stowage_id',u'司机交接单数据')
    report_line_1 = fields.One2many('tms.stowage.report_1','stowage_id',u'配送运输数据')
    all_box_num = fields.Integer(u'保温箱合计', compute='get_all_num')
    all_box_num_1 = fields.Integer(u'保温箱合计', compute='get_all_num')
    all_box_num_2 = fields.Integer(u'保温箱合计', compute='get_all_num')
    all_other_num = fields.Integer(u'其他合计', compute='get_all_num')
    all_other_num_1 = fields.Integer(u'其他合计', compute='get_all_num')
    all_other_num_2 = fields.Integer(u'其他合计', compute='get_all_num')
    all_sum_num = fields.Integer(u'总合计', compute='get_all_num')
    all_sum_num_1 = fields.Integer(u'总合计', compute='get_all_num')
    all_sum_num_2 = fields.Integer(u'总合计', compute='get_all_num')
    is_specially_true = fields.Boolean(u'有专线配送信息', compute='get_is_specially')
    is_specially_false = fields.Boolean(u'有三方物流信息', compute='get_is_specially')

    def get_is_specially(self):
        for ids in self:
            is_specially_true = 0
            is_specially_false = 0
            for line in self.report_line_1:
                if line.is_specially:
                    is_specially_true += 1
                else:
                    is_specially_false += 1
            if is_specially_true > 0:
                ids.is_specially_true = True
            if is_specially_false > 0:
                ids.is_specially_false = True

    # 计算合计数量
    def get_all_num(self):
        for ids in self:
            ids.all_box_num = 0
            ids.all_box_num_1 = 0
            ids.all_box_num_2 = 0
            ids.all_other_num = 0
            ids.all_other_num_1 = 0
            ids.all_other_num_2 = 0
            ids.all_sum_num = 0
            ids.all_sum_num_1 = 0
            ids.all_sum_num_2 = 0
            for line in ids.report_line:
                ids.all_box_num += line.warm_box
                ids.all_other_num += line.other
                ids.all_sum_num += line.sum
            for line in ids.report_line_1:
                if line.is_specially:
                    ids.all_box_num_1 += line.warm_box
                    ids.all_other_num_1 += line.other
                else:
                    ids.all_box_num_2 += line.warm_box
                    ids.all_other_num_2 += line.other
            ids.all_sum_num_1 = ids.all_box_num_1 + ids.all_other_num_1
            ids.all_sum_num_2 = ids.all_box_num_2 + ids.all_other_num_2

    # 计算总合计金额
    def _get_all_money(self):
        for ids in self:
            num = 0.0
            for line in ids.order_line:
                num += line.warm_box_num * line.warm_box_money + line.other_num * line.other_money + line.portal_plus + line.trilateral_logistics
            ids.all_money = num + ids.price.name

    @api.model
    def create(self, vals):
        res_id = super(tms_stowage, self).create(vals)
        now = datetime.now().strftime('%y%m%d')
        stowage_ids = self.search([('date','=',res_id.date)])
        # 获取配载编号
        if not vals.get('name'):
            name = 'F'+ (str(res_id.car_id.location_id.warehouse_num_name) if res_id.car_id.location_id.warehouse_num_name else '') + now + ('0' + str(len(stowage_ids))) if len(str(len(stowage_ids)))==1 else str(len(stowage_ids))
            res_id.write({'name':name})
        return res_id

    @api.multi
    def unlink(self):
        for ids in self:
            if ids.state != 'cancel':
                raise osv.except_osv(_(u'警告'),_(u'只能删除取消的配载单'))
        return super(tms_stowage, self).unlink()

    # 完成
    @api.multi
    def btn_done(self):
        # 生成司机交接单数据
        info_dict = {} #{物流公司:{子编码，门店数，保温箱，其他}}
        info_portal_dict = {} #{物流公司:门店}
        protal_dict = {'1':{},'2':{}} #{专线or三方物流:{门店:{保温箱，其他}}}
        num = 0
        for line in self.order_line:
            all_money = line.warm_box_num * line.warm_box_money + line.other_num * line.other_money + line.trilateral_logistics
            # 如果是专线配送
            if line.logistics_id.is_specially:
                if line.portal_id in protal_dict['1']:
                    protal_dict['1'][line.portal_id]['warm_box'] += line.warm_box_num
                    protal_dict['1'][line.portal_id]['other'] += line.other_num
                    protal_dict['1'][line.portal_id]['all_money'] += all_money
                else:
                    protal_dict['1'][line.portal_id] = {'all_money':all_money,'warm_box':line.warm_box_num,'other':line.other_num}
            else:
                if line.portal_id in protal_dict['2']:
                    protal_dict['2'][line.portal_id]['warm_box'] += line.warm_box_num
                    protal_dict['2'][line.portal_id]['other'] += line.other_num
                    protal_dict['2'][line.portal_id]['all_money'] += all_money
                else:
                    protal_dict['2'][line.portal_id] = {'all_money':all_money,'warm_box':line.warm_box_num,'other':line.other_num}
            if line.logistics_id in info_dict:
                if line.portal_id not in info_portal_dict.values():
                    info_dict[line.logistics_id]['protal_num'] += 1
                info_dict[line.logistics_id]['warm_box'] += line.warm_box_num
                info_dict[line.logistics_id]['other'] += line.other_num
            else:
                num += 1
                name = self.name + ('P' if line.logistics_id.is_specially else 'W') + ('0'+str(num) if len(str(num)) == 1 else str(num))
                info_dict[line.logistics_id] = {'name':name,'protal_num':1,'warm_box':line.warm_box_num,'other':line.other_num}
                info_portal_dict[line.logistics_id] = line.portal_id
        report_line = []
        report_line_1 = []
        for key,value in protal_dict.items():
            if key == '1':
                is_specially = True
            else:
                is_specially = False
            num_1 = 0
            for key1,value1 in value.items():
                num_1 += 1
                report_line_1.append((0,0,{'all_money':value1['all_money'],'is_specially':is_specially,'protal_id':key1.id,'name':num_1,'warm_box':value1['warm_box'],'other':value1['other']}))
        for key,value in info_dict.items():
            report_line.append((0,0,{'logistics_id':key.id,'name':value['name'],'protal_num':value['protal_num'],'warm_box':value['warm_box'],'other':value['other']}))
        return self.write({'state':'done','report_line':report_line,'report_line_1':report_line_1})

    # 取消
    @api.multi
    def btn_cancel(self):
        for line in self.order_line:
            line.picking_id.write({'stowage_id':''})
        return self.write({'state':'cancel'})

    # 打印交车单
    @api.multi
    def btn_print_car_report(self):
        context = dict(self._context or {}, active_ids=self.ids)
        return self.pool["report"].get_action(self._cr, self._uid, self.id, 'qdodoo_TMS.report_tms_car_connect', context=context)

    # 打印配送运输单
    @api.multi
    def btn_print_stowage(self):
        context = dict(self._context or {}, active_ids=self.ids)
        if context.get('log') == '1':
            res_id = self.pool["report"].get_action(self._cr, self._uid, self.id, 'qdodoo_TMS.report_tms_stowage', context=context)
        if context.get('log') == '2':
            res_id = self.pool["report"].get_action(self._cr, self._uid, self.id, 'qdodoo_TMS.report_tms_stowage_line', context=context)
        return res_id

class tms_stowage_line(models.Model):
    """
        配载明细
    """
    _name = 'tms.stowage.line'

    order_id = fields.Many2one('tms.stowage',u'配载')
    logistics_id = fields.Many2one('tms.trilateral.logistics',u'物流公司')
    portal_id = fields.Many2one('res.partner',u'门店')
    warm_box_num = fields.Integer(u'保温箱数')
    other_num = fields.Integer(u'其他数')
    portal_plus = fields.Float(u'门店加收费', compute='get_logistics_num')
    trilateral_logistics = fields.Float(u'物流短驳费', compute='get_logistics_num')
    warm_box_money = fields.Float(u'保温箱费用')
    other_money = fields.Float(u'其他费用')
    picking_id = fields.Many2one('stock.picking',u'调拨单')

    def get_logistics_num(self):
        for ids in self:
            if ids.logistics_id:
                ids.portal_plus = ids.portal_id.portal_plus
                ids.trilateral_logistics = ids.logistics_id.trilateral_add

class tms_stowage_wizard(models.TransientModel):
    """
        选择配载明细wizard
    """
    _name = 'tms.stowage.wizard'

    date_start = fields.Date(u'订单开始时间')
    date_end = fields.Date(u'订单结束时间')
    logistics_id = fields.Many2one('tms.trilateral.logistics',u'物流公司')
    line_id = fields.Many2one('tms.partner.line',u'路线')
    portal_id = fields.Many2many('res.partner','partner_stowage_rel','partner_id','stowage_id',u'门店')
    location_id = fields.Many2one('stock.warehouse',u'物流中心',related='logistics_id.location_id')

    @api.onchange('line_id')
    def onchange_line_id(self):
        if self.line_id:
            self.portal_id = ''
            partner_ids = self.env['res.partner'].search([('tms_line_id','=',self.line_id.id)])
            self.portal_id = [[6,False,partner_ids.ids]]

    @api.multi
    def btn_select(self):
        date_start = datetime.strptime(self.date_start,'%Y-%m-%d')
        date_end = datetime.strptime(self.date_end,'%Y-%m-%d')
        if (date_end-date_start).days > 3:
            raise osv.except_osv(_(u'警告'),_(u'订单区间必须在三天之内！'))
        picking_obj = self.env['stock.picking']
        stowage_line_obj = self.env['tms.stowage.line']
        domain = [('partner_id','=',self.portal_id.ids),('date','>=',self.date_start),('date','<=',self.date_end),('state','not in',('cancel','done')),('stowage_id','=',False)]
        picking_ids = picking_obj.search(domain)
        if not picking_ids:
            raise osv.except_osv(_(u'警告'),_(u'未查询到对应的待出库数据！'))
        for picking_id in picking_ids:
            res_id = stowage_line_obj.create({'other_money':picking_id.partner_id.tms_other,'warm_box_money':picking_id.partner_id.warm_box,'warm_box_num':picking_id.box_num,'picking_id':picking_id.id,'order_id':self._context.get('active_id'),'logistics_id':self.logistics_id.id,'portal_id':picking_id.partner_id.id})
            picking_id.write({'stowage_id':res_id.id})
        return True

class tms_stock_picking_inherit(models.Model):
    """
        库存调拨增加标志字段是否已配载
    """
    _inherit = 'stock.picking'

    stowage_id = fields.Many2one('tms.stowage.line',u'配载明细')

class tms_stowage_report(models.Model):
    """
        司机交接单数据
    """
    _name = 'tms.stowage.report'

    stowage_id = fields.Many2one('tms.stowage',u'配载单')
    logistics_id = fields.Many2one('tms.trilateral.logistics',u'物流公司')
    name = fields.Char(u'子编码')
    protal_num = fields.Integer(u'门店数')
    warm_box = fields.Integer(u'保温箱数')
    other = fields.Integer(u'其他')
    sum = fields.Integer(u'合计', compute='_get_sum')

    # 计算合计
    def _get_sum(self):
        for ids in self:
            ids.sum = ids.warm_box + ids.other

class tms_stowage_report_1(models.Model):
    """
        配送运输明细
    """
    _name = 'tms.stowage.report_1'

    stowage_id = fields.Many2one('tms.stowage',u'配载单')
    protal_id = fields.Many2one('res.partner',u'门店')
    name = fields.Integer(u'编号')
    warm_box = fields.Integer(u'保温箱数')
    other = fields.Integer(u'其他')
    is_specially = fields.Boolean(u'专线配送')
    all_money = fields.Float(u'运费合计')


