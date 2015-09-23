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
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_car_bill_lading(models.Model):
    """
        提单
    """
    _name = 'qdodoo.car.bill.lading'    # 模型名称
    _inherit = ['mail.thread']

    name = fields.Char(u'提单号')
    bill_note = fields.Binary(u'上传提单')
    file_name = fields.Char(u'提单名称')
    in_port = fields.Many2one('qdodoo.shipment.port',u'发货港',domain=[('type','=','in')])
    out_port = fields.Many2one('qdodoo.shipment.port',u'目的港',domain=[('type','=','out')])
    contract_id = fields.Many2one('qdodoo.car.in.contract',u'进口合同号',required=True,domain=[('state','=','in_ship')])
    partner_id = fields.Many2one('res.partner',u'供应商')
    in_partner_id = fields.Many2one('res.partner',u'进口代理商')
    left_ship_date = fields.Date(u'离港日期')
    into_ship_date = fields.Date(u'预计到港日期')
    is_true = fields.Boolean(u'提单是否有效')
    car_number = fields.Float(u'车辆数',compute="_get_car_number")
    order_line = fields.One2many('qdodoo.car.archives','lading_number',u'货物明细')
    user_id = fields.Many2one('res.users',u'跟单员')
    is_one = fields.Boolean(u'是否点击过按钮')

    _defaults = {
        'is_true':True,
        'is_one':False,
        'contract_id':lambda cr, uid, ids, context:context.get('contract_id'),
        'in_port':lambda cr, uid, ids, context:context.get('in_port'),
        'out_port':lambda cr, uid, ids, context:context.get('out_port'),
        'partner_id':lambda cr, uid, ids, context:context.get('partner_id'),
        'in_partner_id':lambda cr, uid, ids, context:context.get('in_partner_id'),
    }

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('qdodoo.car.bill.lading')
        res_id = super(qdodoo_car_bill_lading, self).create(vals)
        if res_id.contract_id and res_id.contract_id.state == 'in_ship':
            res_id.contract_id.write({'state':'except_invoice'})
        for line in res_id.order_line:
            line.write({'contract_id':res_id.contract_id,'agency_id':res_id.contract_id.agency_id})
        return res_id

    def btn_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'is_true':False})

    def btn_create_line(self, cr, uid, ids, context=None):
        payment_obj = self.pool.get('qdodoo.payment.order')
        payment_line_obj = self.pool.get('payment.line')
        obj = self.browse(cr, uid, ids[0])
        line_obj = self.pool.get('qdodoo.car.archives')
        if not obj.contract_id:
            raise osv.except_osv(u'警告', "必须有进口合同号才能使用此功能!")
        else:
            for line in obj.contract_id.order_line:
                for i in range(int(line.product_qty)):
                    payment_ids = payment_obj.search(cr, uid, [('agency_id','=',obj.contract_id.agency_id.id)])
                    price_unit = line.price_unit * (1 - obj.contract_id.deposit_rate/100) * obj.contract_id.agency_id.deposit_rate
                    payment_line_ids = payment_line_obj.search(cr, uid, [('order_id','=',payment_ids[0]),('amount_currency','=',price_unit),('state','!=','cancel')])
                    payment_line_id = payment_line_ids and payment_line_ids[0] or ''
                    line_obj.create(cr, uid, {'lading_number':ids[0],'car_model':line.product_id.id,'payment_id':payment_line_id})
        self.write(cr, uid, ids, {'is_one':True})
        return True

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
    _inherit = ['mail.thread']

    STATE_SELECTION = [
        ('draft', u'赎车申请'),
        ('confirmed', u'代理商确认'),
        ('formulate', u'付款通知'),
        ('signed', u'付款'),
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

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('qdodoo.redeem.car')
        return super(qdodoo_redeem_car, self).create(vals)

    def write(self, cr, uid, ids, valus, context=None):
        if valus.get('state') == 'formulate':
            obj = self.browse(cr, uid, ids[0])
            archives_obj = self.pool.get('qdodoo.car.archives')
            num = []
            for line in obj.order_line:
                num.append(line.car_department.id)
            archives_ids = archives_obj.search(cr, uid, [('id','=',line.car_department.id)])
            for key in archives_obj.browse(cr, uid, archives_ids):
                if key.redeem_apply_number:
                    raise osv.except_osv(u'警告', "存在已赎车的车辆!")
            archives_obj.write(cr, uid, archives_ids,{'redeem_apply_number':ids[0]})
        return super(qdodoo_redeem_car, self).write(cr, uid, ids, valus, context=context)

    def btn_message(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'confirmed'})

    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'cancel'})

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
        obj = self.browse(cr, uid, ids[0])
        archives_obj = self.pool.get('qdodoo.car.archives')
        num = []
        for line in obj.order_line:
            num.append(line.car_department.id)
        archives_ids = archives_obj.search(cr, uid, [('id','=',line.car_department.id),('redeem_apply_number','=',ids[0])])
        archives_obj.write(cr, uid, archives_ids,{'redeem_apply_number':''})
        return self.write(cr, uid, ids, {'state':'confirmed'})

    def btn_payment_message(self, cr, uid, ids, context=None):
        payment_obj = self.pool.get('qdodoo.payment.order')
        line_obj = self.pool.get('payment.line')
        user_obj = self.pool.get('res.users')
        currency = user_obj.browse(cr, uid, uid).company_id.currency_id.id
        obj = self.browse(cr, uid, ids[0])
        payment_new_ids = []
        lst_vals = {}
        payment_new_id = payment_obj.search(cr, uid, [('redeem_id','=',ids[0])])
        if payment_new_id:
            payment_new_ids = payment_new_id
        else:
            for line in obj.order_line:
                payment_ids = payment_obj.search(cr, uid, [('agency_id','=',line.agency_id.id)])
                if payment_ids[0] not in lst_vals:
                    payment_new_ids_new = payment_obj.browse(cr, uid, payment_ids[0]).copy({'redeem_id':ids[0],'agency_id':''})
                    lst_vals[payment_ids[0]] = payment_new_ids_new.id
                else:
                    payment_new_ids_new = payment_obj.browse(cr, uid, lst_vals.get(payment_ids[0]))
                for payment_line in payment_new_ids_new:
                    payment_new_ids.append(payment_line.id)
                    agency_id = line.car_department.payment_id.id
                    line_obj.browse(cr, uid, agency_id).copy({'currency':currency,'name':obj.pool.get('ir.sequence').get(cr, uid, 'payment.line'),'order_id':payment_line.id,'amount_currency':line.redeem_car,})
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
        view_id_form = result_form and result_form[1] or False
        return {
          'name': _('付款通知'),
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
    redeem_car = fields.Float(u'赎车金额')

    def onchange_car_info(self, cr, uid, ids, car_department, context=None):
        obj = self.pool.get('qdodoo.car.archives').browse(cr, uid, car_department)
        values = {}
        values['car_model'] = obj.car_model
        values['agency_id'] = obj.agency_id
        values['redeem_car'] = obj.redeem_car
        return {'value':values}

class qdodoo_settlement_order(models.Model):
    """
        结算单
    """
    _name = 'qdodoo.settlement.order'    # 模型名称
    # _inherits = ['mail.thread']

    STATE_SELECTION = [
        ('draft', u'结算通知'),
        ('confirmed', u'代理商确认'),
        ('formulate', u'付款通知'),
        ('signed', u'收付款'),
        ('done', u'完成'),
        ('cancel', u'已取消')
    ]

    name = fields.Char(u'单号')
    partner_id = fields.Many2one('res.partner',u'进口代理商',required=True)
    date = fields.Date(u'结算日期',readonly=True)
    entrusted_id = fields.Many2one('qdodoo.entrusted.agency',u'委托协议编号',required=True)
    number = fields.Float(u'数量')
    state = fields.Selection(STATE_SELECTION, u'状态', readonly=True,select=True, copy=False)
    notes = fields.Text(u'特别说明')
    order_line_product = fields.One2many('qdodoo.car.archives','settlement_number',u'货物明细')
    order_line_money = fields.One2many('qdodoo.settlement.order.money','order_id',u'费用明细')
    # contract_id = fields.Many2one('qdodoo.car.in.contract',u'进口合同')
    car_number = fields.Float(u'应退（应收）金额合计',compute="_get_car_number")

    _defaults = {
        'date':datetime.now(),
        'state':'draft'
    }

    def onchange_entrusted_id(self, cr, uid, ids, entrusted_id, context=None):
        obj = self.pool.get('qdodoo.entrusted.agency').browse(cr, uid, entrusted_id)
        val = {}
        if entrusted_id:
            val['number'] = len(obj.order_line)
            archives_obj = self.pool.get('qdodoo.car.archives')
            move_line_obj = self.pool.get('account.move.line')
            archives_ids = archives_obj.search(cr, uid, [('agency_id','=',entrusted_id)])
            val['order_line_product'] = archives_obj.browse(cr, uid, archives_ids)
            move_line_ids = move_line_obj.search(cr, uid, [('','',)])
        return {'value': val}

    def _get_car_number(self):
        for ids in self:
            number = 0
            for line in ids.order_line_money:
                number += (line.own_amount - line.in_amount)
            ids.car_number = number

    def btn_message(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'confirmed'})

    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'cancel'})

    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        obj = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids,{'state':'confirmed'})
        return self.pool['report'].get_action(cr, uid, ids, 'purchase.report_purchasequotation', context=context)

    def btn_confirmed(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'formulate'})

    def btn_confirmed_sent(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'confirmed'})

    def btn_payment_message(self, cr, uid, ids, context=None):
        payment_obj = self.pool.get('qdodoo.payment.order')
        payment_id = payment_obj.search(cr, uid, [('settlement_id','=',ids[0])])
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
        view_id_form = result_form and result_form[1] or False
        result_form_model = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_payment_model')
        view_id_form_model = result_form_model and result_form_model[1] or False
        if payment_id:
            return {
              'name': _('付款通知'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.payment.order',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',payment_id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }
        else:
            return {
              'name': _('选择付款方式'),
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'qdodoo.payment.model',
              'type': 'ir.actions.act_window',
              'view_id': [view_id_form_model],
              'context':{'default_model':'settlement_id'},
              'target':'new',
              }

    def wkf_send_rfq(self, cr, uid, ids, context=None):
        if not context:
            context= {}
        ir_model_data = self.pool.get('ir.model.data')
        template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'qdodoo.settlement.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
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

    def write(self, cr, uid, ids, value, context=None):
        if value.get('state') == 'done':
            obj = self.browse(cr, uid, ids[0])
            contract_obj = self.pool.get('qdodoo.car.in.contract')
            entrusted_obj = self.pool.get('qdodoo.entrusted.agency')
            if obj.entrusted_id.contract_id.state == 'in_ship':
                contract_obj.write(cr, uid, [obj.entrusted_id.contract_id.id], {'state':'done'})
            if obj.entrusted_id.state == 'import':
                entrusted_obj.write(cr, uid, [obj.entrusted_id.id], {'state':'done'})
        return super(qdodoo_settlement_order, self).write(cr, uid, ids, value, context=context)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('qdodoo.settlement.order')
        return super(qdodoo_settlement_order, self).create(vals)

class qdodoo_settlement_order_money(models.Model):
    """
        结算单费用明细
    """
    _name = 'qdodoo.settlement.order.money'    # 模型名称

    order_id = fields.Many2one('qdodoo.settlement.order',u'结算单')
    date = fields.Date(u'日期')
    agency_id = fields.Many2one('qdodoo.entrusted.agency',u'项目')
    in_amount = fields.Float(u'收款金额')
    out_amount = fields.Float(u'外币金额')
    exchange_rate = fields.Float(u'汇率')
    own_amount = fields.Float(u'本币金额')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: