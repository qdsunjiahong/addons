# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
import xlrd,base64
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_car_bill_lading(models.Model):
    """
        收获通知单
    """
    _name = 'qdodoo.car.bill.lading'    # 模型名称
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(u'收获通知单号')
    bill_note = fields.Binary(u'收获通知单原件')
    file_name = fields.Char(u'收获通知单名称')
    in_port = fields.Many2one('qdodoo.shipment.port',u'发货港',domain=[('type','=','in')])
    out_port = fields.Many2one('qdodoo.shipment.port',u'目的港',domain=[('type','=','out')])
    contract_id = fields.Many2one('qdodoo.car.in.contract',u'整车采购订单号',required=True,domain=[('state','=','in_ship')])
    contract_new_id = fields.Many2one('qdodoo.car.in.contract.new',u'进口合同号')
    partner_id = fields.Many2one('res.partner',u'供应商')
    in_partner_id = fields.Many2one('res.partner',u'进口代理商')
    left_ship_date = fields.Date(u'发运日期')
    into_ship_date = fields.Date(u'预计到达日期')
    car_number = fields.Float(u'车辆数',compute="_get_car_number")
    order_line = fields.One2many('qdodoo.car.archives','lading_number',u'货物明细')
    user_id = fields.Many2one('res.users',u'跟单员')
    is_one = fields.Boolean(u'是否点击过按钮')
    state = fields.Selection([('draft',u'草稿'),('tra',u'运输'),('done',u'完成'),('cancel',u'取消')],u'状态')
    import_file = fields.Binary(string="导入的模板")

    _defaults = {
        'state':'draft',
        'contract_id':lambda cr, uid, ids, context:context.get('contract_id'),
        'in_port':lambda cr, uid, ids, context:context.get('in_port'),
        'out_port':lambda cr, uid, ids, context:context.get('out_port'),
        'partner_id':lambda cr, uid, ids, context:context.get('partner_id'),
        'in_partner_id':lambda cr, uid, ids, context:context.get('in_partner_id'),
    }

    # 导入功能
    def import_data(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        if wiz.import_file:
            try:
                excel = xlrd.open_workbook(file_contents=base64.decodestring(wiz.import_file))
            except:
                raise osv.except_osv(_(u'提示'), _(u'请使用xls文件进行上传'))
            product_info = excel.sheet_by_index(0)
            archives_obj = self.pool.get('qdodoo.car.archives')
            # company_obj = self.pool.get('res.company')
            # sale_line_obj = self.pool.get('sale.order.line')
            product_obj = self.pool.get('product.product')
            lst = []
            for obj in range(1, product_info.nrows):
                val = {}
                # 获取产品名称
                car_name = product_info.cell(obj, 0).value
                if not car_name:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，车型不能为空')%obj)
                # 查询系统中对应的产品id
                product_id = product_obj.search(cr, uid, [('name', '=', car_name)])
                if not product_id:
                    raise osv.except_osv(_(u'提示'), _(u'系统中没有名称为%s的产品') % car_name)
                # 获取车架号
                car_num = product_info.cell(obj, 1).value
                # 获取车辆金额
                car_money = product_info.cell(obj, 2).value
                if not car_money:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，车辆金额不能为空')%obj)
                # 查询满足条件的货物明细
                archives_ids = archives_obj.search(cr, uid, [('id','not in',lst),('lading_number','=',ids[0]),('name','=',False),('car_model','=',product_id[0]),('car_sale_price','=',car_money)])
                if archives_ids:
                    archives_obj.write(cr, uid, archives_ids[0], {'name':car_num})
                    lst.append(archives_ids[0])
                else:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行数据非法')%obj)
            self.write(cr, uid, [wiz.id], {'import_file': ''})
        else:
            raise osv.except_osv(_(u'提示'), _(u'请先上传模板'))

    @api.model
    def create(self, vals):
        if vals.get('contract_id'):
            res_search = self.search([('contract_id','=',vals.get('contract_id')),('state','=','draft')])
            if res_search:
                raise osv.except_osv(u'警告', "该整车采购单存在草稿状态的收货通知单，无法创建!")
        vals['name'] = self.env['ir.sequence'].get('qdodoo.car.bill.lading')
        res_id = super(qdodoo_car_bill_lading, self).create(vals)
        if res_id.contract_id and res_id.contract_id.state == 'in_ship':
            res_id.contract_id.write({'state':'except_invoice'})
        for line in res_id.order_line:
            line.write({'contract_id':res_id.contract_id,'agency_id':res_id.contract_id.agency_id})
        archives_obj = self.env['qdodoo.car.archives']
        if res_id.contract_id:
            search_ids = archives_obj.search([('contract_id','=',res_id.contract_id.id),('name','=',False)])
            if search_ids:
                search_ids.write({'lading_number':res_id.id})
        return res_id

    # 入运输库位
    def btn_in_tra_stock(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'vpicktree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_form')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('入库单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'stock.picking',
              'type': 'ir.actions.act_window',
              'domain':[('lading_id','=',ids[0])],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 查看入库单
    def btn_car_in_stock_new(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'vpicktree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_form')
        view_id_form = result_form and result_form[1] or False
        picking_obj = self.pool.get('stock.picking')
        res_id = picking_obj.search(cr, uid, ['|',('lading_new_id','=',ids[0]),('lading_id','=',ids[0])])
        return {
              'name': _('入库单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'stock.picking',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',res_id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 收货验车
    def btn_car_in_stock(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'vpicktree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_form')
        view_id_form = result_form and result_form[1] or False
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        res_id = picking_obj.search(cr, uid, [('lading_new_id','=',ids[0]),('state','!=','cancel')])
        if not res_id:
            picking_ids = picking_obj.search(cr, uid, [('lading_id','=',ids[0])])
            res_id = [picking_obj.copy(cr, uid, picking_ids[0],{'lading_id':False,'lading_new_id':ids[0]})]
            for line_key in picking_obj.browse(cr, uid, res_id[0]).move_lines:
                move_obj.write(cr, uid, line_key.id, {'location_id':picking_obj.browse(cr, uid, res_id[0]).picking_type_id.default_location_dest_id.id})
        return {
              'name': _('入库单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'stock.picking',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',res_id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 确认按钮
    def btn_confirmed(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if not obj.bill_note:
            raise osv.except_osv(u'警告', "请上传收货通知单原件!")
        if not obj.left_ship_date:
            raise osv.except_osv(u'警告', "请录入发运日期!")
        if not obj.into_ship_date:
            raise osv.except_osv(u'警告', "请录入预计到达日期!")
        log = 0
        for line in obj.order_line:
            if line.name:
                log = 1
        if log == 0:
            raise osv.except_osv(u'警告', "至少要录入一个车架号!")
        res_id = self.pool.get('qdodoo.car.in.contract').action_picking_create(cr, uid, obj.contract_id.id, ids[0])
        picking_obj = self.pool.get('stock.picking')
        transfer_details_obj = self.pool.get('stock.transfer_details')
        picking_obj.do_enter_transfer_details(cr, uid, [res_id])
        transfer_details_ids = transfer_details_obj.search(cr, uid, [('picking_id','=',res_id)])
        transfer_details_obj.do_detailed_transfer(cr, uid, transfer_details_ids)
        return self.write(cr, uid, ids, {'state':'tra'})

    # 取消按钮
    def btn_cancel(self, cr, uid, ids, context=None):
        archives_obj = self.pool.get('qdodoo.car.archives')
        obj = self.browse(cr, uid, ids[0])
        for line in obj.order_line:
            if line.name:
                archives_obj.write(cr, uid, line.id, {'name':False})
        return self.write(cr, uid, ids, {'state':'draft'})

    # 收货通知单完成，修改对应整车采购协议的状态
    def write(self, cr, uid, ids, valus, context=None):
        super(qdodoo_car_bill_lading, self).write(cr, uid, ids, valus, context=context)
        obj = self.browse(cr, uid, ids[0])
        archives_obj = self.pool.get('qdodoo.car.archives')
        if valus.get('left_ship_date') or valus.get('into_ship_date'):
            left_ship_date = valus.get('left_ship_date') if valus.get('left_ship_date') else obj.left_ship_date
            into_ship_date = valus.get('into_ship_date') if valus.get('into_ship_date') else obj.into_ship_date
            for line in obj.order_line:
                archives_obj.write(cr, uid, [line.id], {'in_port':into_ship_date,'out_port':left_ship_date,})
        return True

    # 获取车辆数
    def _get_car_number(self):
        for ids in self:
            number = 0
            for line in ids.order_line:
                number += 1
            ids.car_number = number

class qdodoo_redeem_car(models.Model):
    """
        赎车
    """
    _name = 'qdodoo.redeem.car'    # 模型名称
    _order = 'id desc'

    STATE_SELECTION = [
        ('draft', u'赎车申请'),
        ('confirmed', u'代理商确认'),
        ('formulate', u'付款申请'),
        ('done', u'完成'),
        ('cancel', u'已取消')
    ]
    name = fields.Char(u'申请单号')
    in_partner_id = fields.Many2one('res.partner',u'进口代理商',required=True)
    date = fields.Date(u'日期',readonly=True)
    order_line = fields.One2many('qdodoo.redeem.car.line','redeem_apply_number',u'货物明细')
    state = fields.Selection(STATE_SELECTION, u'状态', readonly=True,
                                  select=True, copy=False)
    notes = fields.Text(u'特殊要求')

    _defaults = {
        'state':'draft',
        'date':datetime.now().date(),
    }

    # 判断是否出发整车采购的流程
    def write(self, cr, uid, ids, value, context=None):
        if isinstance(ids,(int,long)):
            ids = [ids]
        super(qdodoo_redeem_car, self).write(cr, uid, ids, value, context=context)
        obj = self.browse(cr, uid, ids[0])
        lst_ids = []
        for line in obj.order_line:
            if line.car_department.id not in lst_ids:
                lst_ids.append(line.car_department.id)
            else:
                raise osv.except_osv(u'警告', "不能选择重复的车架号!")
        if value.get('state') == 'done':
            archives_obj = self.pool.get('qdodoo.car.archives')
            contract_obj = self.pool.get('qdodoo.car.in.contract')
            # 获取所有的整车采购单号
            lst = []
            for line in obj.order_line:
                if line.car_department.contract_id.id not in lst:
                    lst.append(line.car_department.contract_id.id)
                archives_obj.write(cr, uid, line.car_department.id, {'redeem_car':line.redeem_car,'redeem_apply_number':ids[0]})
            # 循环所有的整车采购单号，获取车辆档案全部都有赎车单的整车采购单号
            lst_two = []
            for line in lst:
                archives_ids = archives_obj.search(cr, uid, [('contract_id','=',line),('redeem_apply_number','=',False)])
                if not archives_ids:
                    lst_two.append(line)
            # 修改所有整车采购单的状态
            for line in contract_obj.browse(cr, uid, lst_two):
                if line.state == 'car':
                    contract_obj.write(cr, uid, line.id, {'state':'except_invoice'})
        return True

    # 设置序列号
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('qdodoo.redeem.car')
        return super(qdodoo_redeem_car, self).create(vals)

    # 短信
    def btn_message(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'confirmed'})

    # 取消
    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'cancel'})

    # 打印
    def print_quotation(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        self.write(cr, uid, ids,{'state':'confirmed'})
        return self.pool['report'].get_action(cr, uid, ids, 'qdodoo_car_import_trade.report_qdodoo_car_bill_lading', context=context)

    def btn_confirmed(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        for line in obj.order_line:
            if not line.redeem_car:
                raise osv.except_osv(u'警告', "请先输入所有的赎车金额!")
        return self.write(cr, uid, ids, {'state':'formulate'})

    def btn_confirmed_sent(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'confirmed'})

    # 根据业务伙伴的id获取银行账户
    def get_partner_bank(self, cr, uid, ids, partner_id, context=None):
        partner_obj = self.pool.get('res.partner')
        bank_ids = partner_obj.browse(cr, uid, partner_id).bank_ids
        if bank_ids:
            for bank_id in bank_ids:
                if bank_id.is_defaults:
                    return bank_id.id
            return bank_ids[0].id
        return False

    # 付款通知单
    def btn_payment_message(self, cr, uid, ids, context=None):
        payment_obj = self.pool.get('qdodoo.payment.order')
        line_obj = self.pool.get('payment.line')
        users_obj = self.pool.get('res.users')
        obj = self.browse(cr, uid, ids[0])
        payment_new_ids = []
        lst_vals = {}
        payment_new_id = payment_obj.search(cr, uid, [('redeem_id','=',ids[0])])
        if payment_new_id:
            payment_new_ids = payment_new_id
        else:
            # 查询所有的委托协议及对应金额
            key_agency = {}
            for line in obj.order_line:
                if line.agency_id.name in key_agency:
                    key_agency[line.agency_id.name] += line.redeem_car
                else:
                    key_agency[line.agency_id.name] = line.redeem_car
            # 创建一个付款通知单
            vals = {}
            vals['payment_supplier'] = obj.in_partner_id.id
            vals['user_id'] = uid
            vals['partner_qdodoo_id'] = obj.in_partner_id.id
            vals['date_prefered'] = 'due'
            vals['redeem_id'] = obj.id
            res_id = payment_obj.create(cr, uid, vals, context=context)
            payment_new_ids.append(res_id)
            for key_name in key_agency:
                val = {}
                val['order_id'] = res_id
                val['date'] = datetime.now().date()
                val['partner_id'] = obj.in_partner_id.id
                val['currency'] = users_obj.browse(cr, uid, uid).company_id.currency_id.id
                val['communication'] = key_name
                val['communication2'] = u'赎车款 单号:%s'%obj.name
                val['bank_id'] = self.get_partner_bank(cr, uid, ids, obj.in_partner_id.id)
                val['name'] = obj.pool.get('ir.sequence').get(cr, uid, 'payment.line')
                val['state'] = 'normal'
                val['amount_currency'] = key_agency.get(key_name)
                line_obj.create(cr, uid, val, context=None)
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
        view_id_form = result_form and result_form[1] or False
        return {
          'name': _('付款申请'),
          'view_type': 'form',
          "view_mode": 'tree,form',
          'res_model': 'qdodoo.payment.order',
          'type': 'ir.actions.act_window',
          'domain':[('id','in',payment_new_ids)],
          'views': [(view_id,'tree'),(view_id_form,'form')],
          'view_id': [view_id],
          }

    def wkf_send_rfq(self, cr, uid, ids, context=None):
        if not context:
            context= {}
        state = self.browse(cr, uid, ids[0]).state
        ir_model_data = self.pool.get('ir.model.data')
        template_id = ir_model_data.get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'email_template_redeem_id')[1]
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'qdodoo.redeem.car',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_state': state,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

class qdodoo_redeem_car_line(models.Model):
    """
        赎车明细
    """
    _name = 'qdodoo.redeem.car.line'    # 模型名称

    redeem_apply_number = fields.Many2one('qdodoo.redeem.car',u'赎车单')
    car_department = fields.Many2one('qdodoo.car.archives',u'车架号',required=True)
    car_model = fields.Many2one('product.product',u'车型')
    agency_id = fields.Many2one('qdodoo.entrusted.agency',u'委托协议')
    import_number = fields.Many2one('qdodoo.car.in.contract.new',u'进口合同号')
    redeem_car = fields.Float(u'赎车金额')

    def onchange_car_info(self, cr, uid, ids, car_department, context=None):
        obj = self.pool.get('qdodoo.car.archives').browse(cr, uid, car_department)
        values = {}
        values['car_model'] = obj.car_model.id
        values['agency_id'] = obj.agency_id.id
        values['redeem_car'] = obj.redeem_car
        values['import_number'] = obj.import_number.id
        return {'value':values}

class qdodoo_settlement_order(osv.osv_memory):
    """
        结算单
    """
    _name = 'qdodoo.settlement.order'    # 模型名称
    # _inherits = ['mail.thread']

    # STATE_SELECTION = [
    #     ('draft', u'草稿'),
    #     ('confirmed', u'确认'),
    #     ('formulate', u'付款通知'),
    #     ('signed', u'财务付款'),
    #     ('done', u'完成'),
    #     ('cancel', u'已取消')
    # ]

    ref = fields.Char(u'付款事由')
    partner_id = fields.Many2one('res.partner',u'合作伙伴',required=True)
    date = fields.Date(u'日期',readonly=True)
    # entrusted_id = fields.Many2one('qdodoo.entrusted.agency',u'委托协议号')
    contract_id = fields.Many2one('qdodoo.car.in.contract',u'整车采购号')
    # contract_new_id = fields.Many2one('qdodoo.car.in.contract.new',u'进口合同号')
    account_id = fields.Many2one('account.analytic.account',u'辅助核算项')
    # number = fields.Float(u'数量')
    # state = fields.Selection(STATE_SELECTION, u'状态', readonly=True,select=True, copy=False)
    # notes = fields.Text(u'特别说明')
    # order_line_product = fields.One2many('qdodoo.car.archives','settlement_number',u'货物明细')
    # order_line_money = fields.One2many('qdodoo.settlement.order.money','order_id',u'费用明细')
    # contract_id = fields.Many2one('qdodoo.car.in.contract',u'进口合同')
    # car_number = fields.Float(u'应退（应收）金额合计',compute="_get_car_number")
    currency_id = fields.Many2one('res.currency',u'外币币种')
    in_amount = fields.Float(u'预付金额（本币）')
    out_amount = fields.Float(u'应付金额（外币）')
    exchange_rate = fields.Float(u'汇率')
    own_amount = fields.Float(u'应付金额（本币）')

    _defaults = {
        'date':datetime.now(),
        # 'state':'draft'
    }

    # def _get_car_number(self):
    #     for ids in self:
    #         number = 0
    #         for line in ids.order_line_money:
    #             number += (line.own_amount - line.in_amount)
    #         ids.car_number = number
    #
    # def btn_message(self, cr, uid, ids, context=None):
    #     return self.write(cr, uid, ids, {'state':'confirmed'})
    #
    # def action_cancel(self, cr, uid, ids, context=None):
    #     return self.write(cr, uid, ids, {'state':'cancel'})
    #
    # def print_quotation(self, cr, uid, ids, context=None):
    #     '''
    #     This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow
    #     '''
    #     assert len(ids) == 1, 'This option should only be used for a single id at a time'
    #     obj = self.browse(cr, uid, ids[0])
    #     self.write(cr, uid, ids,{'state':'confirmed'})
    #     return self.pool['report'].get_action(cr, uid, ids, 'purchase.report_purchasequotation', context=context)
    #
    # def btn_confirmed(self, cr, uid, ids, context=None):
    #     return self.write(cr, uid, ids, {'state':'formulate'})
    #
    # def btn_confirmed_sent(self, cr, uid, ids, context=None):
    #     return self.write(cr, uid, ids, {'state':'confirmed'})
    #
    # # 根据业务伙伴的id获取银行账户
    # def get_partner_bank(self, cr, uid, ids, partner_id, context=None):
    #     partner_obj = self.pool.get('res.partner')
    #     bank_ids = partner_obj.browse(cr, uid, partner_id).bank_ids
    #     if bank_ids:
    #         for bank_id in bank_ids:
    #             if bank_id.is_defaults:
    #                 return bank_id.id
    #         return bank_ids[0].id
    #     return False
    #
    # # 收付款通知
    # def btn_payment_message(self, cr, uid, ids, context=None):
    #     obj = self.browse(cr, uid, ids[0])
    #     payment_obj = self.pool.get('qdodoo.payment.order')
    #     users_obj = self.pool.get('res.users')
    #     line_obj = self.pool.get('payment.line')
    #     payment_id = payment_obj.search(cr, uid, [('settlement_id','=',ids[0])])
    #     result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
    #     view_id = result and result[1] or False
    #     result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
    #     view_id_form = result_form and result_form[1] or False
    #     if not payment_id:
    #         # 创建一个付款通知单
    #         vals = {}
    #         vals['payment_supplier'] = obj.partner_id.id
    #         vals['user_id'] = uid
    #         vals['partner_qdodoo_id'] = obj.partner_id.id
    #         vals['date_prefered'] = 'due'
    #         vals['settlement_id'] = obj.id
    #         val = {}
    #         val['date'] = datetime.now().date()
    #         val['partner_id'] = obj.partner_id.id
    #         val['currency'] = users_obj.browse(cr, uid, uid).company_id.currency_id.id
    #         val['communication'] = obj.name
    #         val['communication2'] = '结算'
    #         val['bank_id'] = self.get_partner_bank(cr, uid, ids, obj.partner_id.id)
    #         val['name'] = obj.pool.get('ir.sequence').get(cr, uid, 'payment.line')
    #         val['state'] = 'normal'
    #         if obj.car_number > 0:
    #             vals['pay_type'] = 'out'
    #             res_id = payment_obj.create(cr, uid, vals, context=context)
    #             payment_id.append(res_id)
    #             val['order_id'] = res_id
    #             val['amount_currency'] = obj.car_number
    #             line_obj.create(cr, uid, val, context=None)
    #         if obj.car_number < 0:
    #             vals['pay_type'] = 'in'
    #             res_id = payment_obj.create(cr, uid, vals, context=context)
    #             payment_id.append(res_id)
    #             val['order_id'] = res_id
    #             val['amount_currency'] = -obj.car_number
    #             line_obj.create(cr, uid, val, context=None)
    #     return {
    #       'name': _('付款通知'),
    #       'view_type': 'form',
    #       "view_mode": 'tree,form',
    #       'res_model': 'qdodoo.payment.order',
    #       'type': 'ir.actions.act_window',
    #       'domain':[('id','in',payment_id)],
    #       'views': [(view_id,'tree'),(view_id_form,'form')],
    #       'view_id': [view_id],
    #       }
    #
    # def wkf_send_rfq(self, cr, uid, ids, context=None):
    #     if not context:
    #         context= {}
    #     state = self.browse(cr, uid, ids[0]).state
    #     ir_model_data = self.pool.get('ir.model.data')
    #     template_id = False
    #     try:
    #         compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
    #     except ValueError:
    #         compose_form_id = False
    #     ctx = dict(context)
    #     ctx.update({
    #         'default_model': 'qdodoo.settlement.order',
    #         'default_res_id': ids[0],
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         'default_state': state,
    #         'default_composition_mode': 'comment',
    #     })
    #     return {
    #         'name': _('Compose Email'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(compose_form_id, 'form')],
    #         'view_id': compose_form_id,
    #         'target': 'new',
    #         'context': ctx,
    #     }
    #
    # def write(self, cr, uid, ids, value, context=None):
    #     res_id = super(qdodoo_settlement_order, self).write(cr, uid, ids, value, context=context)
    #     if value.get('state') == 'done':
    #         obj = self.browse(cr, uid, ids[0])
    #         contract_obj = self.pool.get('qdodoo.car.in.contract')
    #         contract_ids = self.search(cr, uid, [('contract_id','=',obj.contract_id.id),('state','not in',('done','cancel'))])
    #         # entrusted_obj = self.pool.get('qdodoo.entrusted.agency')
    #         if obj.contract_id.state == 'except_invoice' and not contract_ids:
    #             contract_obj.write(cr, uid, [obj.contract_id.id], {'state':'no_money'})
    #         # if obj.entrusted_id.state == 'import':
    #         #     entrusted_obj.write(cr, uid, [obj.entrusted_id.id], {'state':'done'})
    #     return res_id
    #
    # @api.model
    # def create(self, vals):
    #     vals['name'] = self.env['ir.sequence'].get('qdodoo.settlement.order')
    #     return super(qdodoo_settlement_order, self).create(vals)

# class qdodoo_settlement_order_money(models.Model):
#     """
#         结算单费用明细
#     """
#     _name = 'qdodoo.settlement.order.money'    # 模型名称
#
#     order_id = fields.Many2one('qdodoo.settlement.order',u'结算单')
#     date = fields.Date(u'日期')
#     notes = fields.Char(u'摘要')
#     in_amount = fields.Float(u'金额（预付）')
#     out_amount = fields.Float(u'外币金额（应付）')
#     exchange_rate = fields.Float(u'汇率（应付）')
#     own_amount = fields.Float(u'本币金额（应付）')
#
#     def onchange_get_own_money(self, cr, uid, ids, out_amount,exchange_rate, context=None):
#         if out_amount and exchange_rate:
#             return {'value':{'own_amount':out_amount*exchange_rate}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: