# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
import time
from openerp.tools.translate import _
from datetime import timedelta, datetime
from openerp.exceptions import ValidationError
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_purchase_order_line_inherit(models.Model):
    _inherit = 'purchase.order.line'

    entrusted_id = fields.Many2one('qdodoo.entrusted.agency',u'委托协议')
    product_amount = fields.Float(u'货值小计',compute="_get_product_amount")
    agency_amount = fields.Float(u'代理费小计（元）',compute="_get_agency_amount")
    agency_fee = fields.Float(u'每台车代理费(元)')

    def _get_product_amount(self):
        for line in self:
            line.product_amount = line.product_qty * line.price_unit
    def _get_agency_amount(self):
        for line in self:
            if line.agency_fee:
                line.agency_amount = line.product_qty * line.agency_fee

class qdodoo_entrusted_agency(models.Model):
    """
        委托代理
    """
    _name = 'qdodoo.entrusted.agency'    # 模型名称
    _inherit = ['mail.thread']
    _order = 'id desc'

    STATE_SELECTION = [
        ('draft', u'草稿'),
        ('confirmed', u'委托确认'),
        ('formulate', u'协议拟定'),
        ('signed', u'协议会签'),
        ('margin', u'预付款'),
        ('import', u'协议执行'),
        ('done', u'完成'),
        ('cancel', u'已取消')
    ]
    name = fields.Char(u'委托协议号')
    contract_id = fields.Many2one('qdodoo.car.in.contract',u'采购订单号',required=True, domain=[('is_type','=','contract')])
    date = fields.Datetime(u'委托申请日期')
    agency_date = fields.Datetime(u'协议签订日期')
    partner_id = fields.Many2one('res.partner',u'供应商')
    in_port = fields.Many2one('qdodoo.shipment.port',u'发货港',domain=[('type','=','in')])
    agent_id = fields.Many2one('res.partner',u'进口代理商')
    out_port = fields.Many2one('qdodoo.shipment.port',u'目的港',domain=[('type','=','out')])
    agent_declaration_id = fields.Many2one('res.partner',u'代理报关公司')
    partial_shipment = fields.Selection([('ALLOWED','ALLOWED'),('NOT ALLOWED','NOT ALLOWED')],u'分批发运')
    trans_shipment = fields.Selection([('ALLOWED','ALLOWED'),('NOT ALLOWED','NOT ALLOWED')],u'转运')
    agent_ciq_id = fields.Many2one('res.partner',u'代理报检公司')
    purchase_type = fields.Selection([('agency_in',u'委托进口'),('own_in',u'自营进口'),('own',u'内贸自营采购')],u'采购渠道')
    payment_type = fields.Many2one('qdodoo.payment.type',u'付款方式')
    open_date = fields.Date(u'预计开证日期')
    shipment_date = fields.Date(u'最迟发运日期')
    payment_line = fields.Many2one('qdodoo.payment.line',u'价格条款')
    insurance_type = fields.Char(u'购买保险险种')
    order_line = fields.One2many('purchase.order.line','entrusted_id',u'货物明细')
    notes = fields.Text(u'特殊要求')
    car_number = fields.Float(u'数量',compute="_get_car_number")
    car_money = fields.Float(u'总金额',compute="_get_car_money")
    pricelist_id = fields.Many2one('product.pricelist', u'价格表')
    state = fields.Selection(STATE_SELECTION, u'状态', readonly=True,
                                  select=True, copy=False)
    currency_id = fields.Many2one('res.currency',u'车辆价格币别')
    company_id = fields.Many2one('res.company',u'公司')
    deposit_rate = fields.Float(u'合同定金金额')
    contract_note = fields.Binary(u'委托协议原件')
    file_name = fields.Char(u'协议名称')
    analytic_id = fields.Many2one('account.analytic.account',u'辅助核算项',copy=False)
    is_payment = fields.Boolean(u'是否确认付款',copy=False)
    import_contract_number = fields.Char(u'进口合同号')
    customer_id = fields.Many2one('res.partner',u'收货人')
    receive_id = fields.Many2one('res.partner',u'买方')
    purchase_type = fields.Selection([('agency_in',u'委托进口'),('own_in',u'自营进口'),('own',u'内贸自营采购')],u'采购渠道')
    deposit_margin = fields.Boolean(u'定金既履约保证金')
    margin_own = fields.Boolean(u'定金/保证金独立委托')
    deposit_margin_customer = fields.Many2one('res.partner',u'履约保证金受托方')
    margin_log = fields.Boolean(u'定金/保证金委托标识')
    agent_template = fields.Many2one('qdodoo.contract.template',u'协议模板')
    margin_rate = fields.Float(u'委托保证金比例(%)')
    margin_rate_money = fields.Float(u'委托保证金金额(元)')
    out_contract_text = fields.Char(u'外贸进口合同文本')
    payment_old = fields.Float(u'已付款',compute="_get_all_sum")
    all_sum = fields.Float(u'合计',compute="_get_all_sum")
    agency_num = fields.Float(u'委托金额',compute="_get_all_sum")
    new_pay = fields.Boolean(u'定金/保证金委托支付')
    agency_number = fields.Char(u'协议编号')

    def btn_confirmed(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'signed'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('qdodoo.entrusted.agency')
        return super(qdodoo_entrusted_agency, self).create(vals)

    # 获取当前登录用户的公司对应的客户
    def get_customer_id(self, cr, uid, ids, context=None):
        obj = self.pool.get('res.users')
        return obj.browse(cr, uid, uid).company_id.partner_id.id

    _defaults = {
        'customer_id':get_customer_id,
        'receive_id':get_customer_id,
        'date':datetime.now(),
        'is_payment':False,
        'new_pay':False,
        'state':'draft',
        'currency_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id,
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
    }
    # 查看进口合同
    def btn_read_contract(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_car_in_contract_new')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_car_in_contract_new')
        view_id_form = result_form and result_form[1] or False
        obj = self.browse(cr, uid, ids[0])
        return {
              'name': _('进口合同'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.in.contract.new',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',obj.contract_id.new_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 获取代理商的采购价格表
    def onchange_agent_pricelist(self, cr, uid, ids, agent_id, context=None):
        if agent_id:
            obj = self.pool.get('res.partner').browse(cr, uid, agent_id)
            return {'value': {
            'pricelist_id': obj.property_product_pricelist_purchase and obj.property_product_pricelist_purchase.id or False,
            }}
        return {'value':{}}

    # 计算合计、已付金额、委托金额
    def _get_all_sum(self):
        money = 0
        for line in self:
            if not line.deposit_margin:
                if not line.new_pay:
                    money = line.deposit_rate
            line.payment_old = money
            num = 0
            for line_new in line.order_line:
                num += line_new.product_qty * line_new.price_unit
            line.all_sum = num
            line.agency_num = num - money

    def onchange_money(self, cr, uid, ids, margin_rate, agency_num, context=None):
        if margin_rate:
            obj = self.browse(cr, uid, ids[0])
            return {'value': {
            'margin_rate_money': agency_num * margin_rate /100/obj.currency_id.rate_silent*obj.company_id.currency_id.rate_silent,
            }}
        return {'value':{}}

    def btn_in_ship(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
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
              'domain':[('contract_id','=',obj.contract_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    def btn_redeem(self, cr, uid, ids, context=None):
        lst_obj = []
        line_obj = self.pool.get('qdodoo.redeem.car.line')
        line_obj_ids = line_obj.search(cr, uid, [('agency_id','=',ids[0])])
        for line_obj_id in line_obj.browse(cr, uid, line_obj_ids):
            if line_obj_id.redeem_apply_number.id not in lst_obj:
                lst_obj.append(line_obj_id.redeem_apply_number.id)
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_redeem_car')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_redeem_car')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('赎车单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.redeem.car',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',lst_obj)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    def btn_rejected(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'signed'})

    def unlink(self, cr, uid, ids, context=None):
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        for id in ids:
            contract_ids = contract_obj.search(cr, uid, [('agency_id','=',id)])
            if contract_ids:
                contract_obj.write(cr, uid, contract_ids,{'agency_id':''})
        return super(qdodoo_entrusted_agency,self).unlink(cr, uid, ids, context=context)

    # 编辑方法
    def write(self, cr, uid, ids, value, context=None):
        if isinstance(ids,(int,long)):
            ids = [ids]
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        obj = self.browse(cr, uid, ids[0])
        lst = []
        for line in obj.order_line:
            lst.append(line.id)
        purchase_obj = self.pool.get('purchase.order.line')
        if value.get('state') == 'done':
            res_id = self.search(cr, uid, [('state','=','done'),('contract_id','=',obj.contract_id.id)])
            if res_id:
                raise osv.except_osv(_('错误!'), _('此合同已存在完成的委托协议！'))
        if value.get('state') == 'import':
            if not obj.new_pay:
                if obj.contract_id.state == 'except_picking':
                    contract_obj.write(cr, uid, obj.contract_id.id, {'state':'customs','agency_id':ids[0]})
            else:
                contract_obj.write(cr, uid, obj.contract_id.id, {'state':'lc'})
        if value.get('state') == 'formulate':
            purchase_obj.write(cr, uid, lst, {'state':'done'})
        margin_own = value.get('margin_own') if value.get('margin_own') else obj.margin_own
        # 如果委托协议取消
        if value.get('state') == 'cancel':
            contract_ids = contract_obj.search(cr, uid, [('agency_id','=',obj.id)])
            if contract_ids:
                contract_obj.write(cr, uid, contract_ids,{'agency_id':''})
        # 如果委托协议确定后
        if value.get('state') == 'signed':
            purchase_obj.write(cr, uid, lst, {'state':'confirmed'})
            if obj.state == 'draft':
                if margin_own and not obj.margin_log:
                    new_id = obj.copy({'margin_log':True})
                    for line_key in obj.order_line:
                        line_key.copy({'entrusted_id':new_id.id })
        return super(qdodoo_entrusted_agency, self).write(cr, uid, ids, value, context=context)

    def btn_read_payment_order(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('付款单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.payment.order',
              'type': 'ir.actions.act_window',
              'domain':[('agency_id','in',ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    def btn_read_entrusted_agency(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_redeem_car')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_redeem_car')
        view_id_form = result_form and result_form[1] or False
        ids_lst = []
        redeem_line_obj = self.pool.get('qdodoo.redeem.car.line')
        redeem_line_ids = redeem_line_obj.search(cr, uid, [('agency_id','in',ids)])
        for line in redeem_line_obj.browse(cr, uid, redeem_line_ids):
            if line.order_id.id not in ids_lst:
                ids_lst.append(line.order_id.id)
        return {
              'name': _('赎车'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.redeem.car',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',ids_lst)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 付款通知
    def btn_payment_message(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        # 代理费合计
        sum = 0
        for line in obj.order_line:
            sum += line.agency_amount
        if not obj.margin_rate_money and not sum:
            return self.write(cr, uid, ids[0], {'state':'import'})
        payment_obj = self.pool.get('qdodoo.payment.order')
        payment_id = payment_obj.search(cr, uid, [('agency_id','=',ids[0])])
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
        view_id_form = result_form and result_form[1] or False
        if not payment_id:
            context['default_model'] = 'agency_id'
            payment_id = self.pool.get('qdodoo.payment.model').search_date(cr, uid, ids, context=context)
        return {
          'name': _('付款申请'),
          'view_type': 'form',
          "view_mode": 'tree,form',
          'res_model': 'qdodoo.payment.order',
          'type': 'ir.actions.act_window',
          'domain':[('id','in',payment_id)],
          'views': [(view_id,'tree'),(view_id_form,'form')],
          'view_id': [view_id],
          }

    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        """Collects require data from purchase order line that is used to create invoice line
        for that purchase order line
        :param account_id: Expense account of the product of PO line if any.
        :param browse_record order_line: Purchase order line browse record
        :return: Value for fields of invoice lines.
        :rtype: dict
        """
        return {
            'name': order_line.name,
            'account_id': account_id,
            'price_unit': order_line.price_unit or 0.0,
            'quantity': order_line.product_qty,
            'product_id': order_line.product_id.id or False,
            'uos_id': order_line.product_uom.id or False,
            'invoice_line_tax_id': [(6, 0, [x.id for x in order_line.taxes_id])],
            'account_analytic_id': order_line.account_analytic_id.id or False,
            'purchase_line_id': order_line.id,
        }

    def _choose_account_from_po_line(self, cr, uid, po_line, context=None):
        fiscal_obj = self.pool.get('account.fiscal.position')
        property_obj = self.pool.get('ir.property')
        if po_line.product_id:
            acc_id = po_line.product_id.property_account_expense.id
            if not acc_id:
                acc_id = po_line.product_id.categ_id.property_account_expense_categ.id
            if not acc_id:
                raise osv.except_osv(_('Error!'), _('Define an expense account for this product: "%s" (id:%d).') % (po_line.product_id.name, po_line.product_id.id,))
        else:
            acc_id = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category', context=context).id
        fpos = False
        return fiscal_obj.map_account(cr, uid, fpos, acc_id)

    def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
        """Prepare the dict of values to create the new invoice for a
           purchase order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: purchase.order record to invoice
           :param list(int) line_ids: list of invoice line IDs that must be
                                      attached to the invoice
           :return: dict of value to create() the invoice
        """
        journal_ids = self.pool['account.journal'].search(
                            cr, uid, [('type', '=', 'purchase')],
                            limit=1)
        if not journal_ids:
            raise osv.except_osv(
                _('Error!'),
                _('Define purchase journal for this company: "%s" (id:%d).') % \
                    (order.company_id.name, order.company_id.id))
        return {
            'name': order.name,
            'reference': order.name,
            'account_id': order.partner_id.property_account_payable.id,
            'type': 'in_invoice',
            'partner_id': order.partner_id.id,
            'currency_id': order.currency_id.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'invoice_line': [(6, 0, line_ids)],
            'origin': order.name,
            'fiscal_position': False,
            'payment_term': False,
            'company_id': order.company_id.id,
        }

    def btn_import_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'done'})

    # 创建发票
    def action_invoice_create(self, cr, uid, ids, res_id=False, context=None):
        """
            创建发票
        """
        context = dict(context or {})

        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        product_obj = self.pool.get('product.product')
        product_ids = product_obj.browse(cr, uid, 1)
        res = False
        account = product_ids.property_account_income.id or product_ids.categ_id.property_account_income_categ.id
        for order in self.browse(cr, uid, ids, context=context):
            # 获取总代理费
            sum = 0
            for line in order.order_line:
                sum += line.agency_amount
            context.pop('force_company', None)
            inv_lines = []
            inv_line_data = {}
            inv_line_data['name'] = product_ids.partner_ref
            if account:
                inv_line_data['account_id'] = account
            inv_line_data['product_id'] = 1
            inv_line_data['quantity'] = 1
            inv_line_data['account_analytic_id'] = res_id
            inv_line_data['price_unit'] = sum
            inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
            inv_lines.append(inv_line_id)
            for po_line in order.order_line:
                po_line.write({'invoice_lines': [(4, inv_line_id)]})

            # get invoice data and create invoice
            inv_data = self._prepare_invoice(cr, uid, order, inv_lines, context=context)
            inv_data['date_invoice'] = datetime.now().date()
            inv_data['partner_id'] = order.agent_id.id
            inv_data['currency_id'] = order.company_id.currency_id.id
            inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            # compute the invoice
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            # Link this new invoice to related purchase order
            order.write({'invoice_ids': [(4, inv_id)]})
            res = inv_id
        return res

    # 根据时间获取对应会计区间
    def get_period_id(self, cr, uid, ids, date, context=None):
        period_obj = self.pool.get('account.period')
        period_ids = period_obj.search(cr, uid, [('date_start','<=',date),('date_stop','>=',date),('special','=',False)])
        if not period_ids:
            raise osv.except_osv(_('错误!'), _('缺少正在使用的会计区间！'))
        return period_ids[0]

    # 查看账务（财务分录）
    def btn_read_payment_order(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_line_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_line_form')
        view_id_form = result_form and result_form[1] or False
        obj = self.browse(cr, uid, ids[0])
        return {
              'name': _('账务分录'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'account.move.line',
              'type': 'ir.actions.act_window',
              'domain':[('analytic_account_id','=',obj.analytic_id.id),('analytic_account_id','!=',False)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 确认协议
    def confirm_contract(self, cr, uid, ids, context=None):
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        contract_new_obj = self.pool.get('qdodoo.car.in.contract.new')
        obj = self.browse(cr, uid, ids[0])
        if not obj.contract_note:
            raise osv.except_osv(_('警告!'), _('请先上传协议原件！'))
        if not obj.agency_date:
            raise osv.except_osv(_('警告!'), _('请先选择协议签订日期！'))
        if not obj.import_contract_number:
            raise osv.except_osv(_('警告!'), _('对应的进口合同未签订！'))
        self.write(cr, uid, ids, {'receive_id':obj.agent_id.id})
        contract_obj.write(cr, uid, obj.contract_id.id, {'receive_id':obj.agent_id.id})
        contract_new_obj.write(cr, uid, obj.contract_id.new_id.id, {'receive_id':obj.agent_id.id})
        # 创建会计分录
        move_obj = self.pool.get('account.move')
        invoice_obj = self.pool.get('account.invoice')
        account_obj = self.pool.get('account.account')
        move_line_obj = self.pool.get('account.move.line')
        # 创建辅助核算项
        location_model_cus, location_cus_ids = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'ir_cron_account_analytic_agency')
        analytic_obj = self.pool.get('account.analytic.account')
        val = {}
        val['name'] = obj.contract_id.new_id.contract_number + '-' + obj.name
        val['type'] = 'normal'
        val['parent_id'] = location_cus_ids
        res_id = analytic_obj.create(cr, uid, val)
        # 查询进口合同的状态
        if obj.contract_id.new_id.state not in ('draft','confirmed','cancel'):
            account_ids = account_obj.search(cr, uid, [('type','=','receivable')],order='id')
            invoice_obj_obj = invoice_obj.browse(cr, uid, obj.contract_id.invoice_id.id)
            obj_sequence = self.pool.get('ir.sequence')
            c = {'fiscalyear_id': invoice_obj_obj.period_id.fiscalyear_id.id}
            new_name = obj_sequence.next_by_id(cr, uid, invoice_obj_obj.journal_id.sequence_id.id, c)
            value = {}
            value['journal_id'] = invoice_obj_obj.journal_id.id
            value['period_id'] = self.get_period_id(cr, uid, ids, invoice_obj_obj.date_invoice)
            value['ref'] = obj.contract_id.new_id.name
            value['date'] = datetime.now().date()
            value['name'] = new_name
            res_move_id = move_obj.create(cr, uid, value)
            vale = {}
            vale['move_id'] = res_move_id
            vale['ref'] = obj.contract_id.new_id.name
            vale['journal_id'] = invoice_obj_obj.journal_id.id
            vale['period_id'] = self.get_period_id(cr, uid, ids, invoice_obj_obj.date_invoice)
            vale['quantity'] = 1
            vale['date'] = invoice_obj_obj.date_invoice
            vale['invoice'] = invoice_obj_obj.id
            vale['currency_id'] = obj.currency_id.id
            if obj.margin_log:
                contract_obj.write(cr, uid, obj.contract_id.id, {'deposit_margin_customer':obj.deposit_margin_customer.id})
                vale['amount_currency'] = obj.deposit_rate
                vale['credit'] = 0
                if obj.deposit_margin:
                    vale['name'] = u'垫付履约保证金'
                else:
                    vale['name'] = u'垫付进口合同定金'
                vale['account_id'] = invoice_obj_obj.account_id.id
                vale['debit'] = obj.deposit_rate/obj.currency_id.rate_silent*obj.company_id.currency_id.rate_silent
                vale['analytic_account_id'] = res_id
                vale['partner_id'] = obj.partner_id.id
                move_line_obj.create(cr, uid, vale)
                vale['debit'] = 0
                vale['credit'] = obj.deposit_rate/obj.currency_id.rate_silent*obj.company_id.currency_id.rate_silent
                vale['amount_currency'] = -obj.deposit_rate
                vale['partner_id'] = obj.deposit_margin_customer.id
                vale['account_id'] = invoice_obj_obj.account_id.id
                move_line_obj.create(cr, uid, vale)
                return self.write(cr, uid, ids, {'state':'import','analytic_id':res_id})
            else:
                if obj.new_pay and not obj.margin_own:
                    contract_obj.write(cr, uid, obj.contract_id.id, {'deposit_margin_customer':obj.receive_id.id})
                    vale['amount_currency'] = obj.deposit_rate
                    vale['debit'] = obj.deposit_rate/obj.currency_id.rate_silent*obj.company_id.currency_id.rate_silent
                    vale['credit'] = 0
                    if obj.deposit_margin:
                        vale['name'] = u'垫付履约保证金'
                    else:
                        vale['name'] = u'垫付进口合同定金'
                    vale['account_id'] = invoice_obj_obj.account_id.id
                    vale['analytic_account_id'] = res_id
                    vale['partner_id'] = obj.partner_id.id
                    move_line_obj.create(cr, uid, vale)
                    vale['amount_currency'] = -obj.deposit_rate
                    vale['debit'] = 0
                    vale['partner_id'] = obj.agent_id.id
                    vale['credit'] = obj.deposit_rate/obj.currency_id.rate_silent*obj.company_id.currency_id.rate_silent
                    vale['account_id'] = invoice_obj_obj.account_id.id
                    move_line_obj.create(cr, uid, vale)
                vale['amount_currency'] = obj.agency_num
                vale['account_id'] = invoice_obj_obj.account_id.id
                vale['partner_id'] = obj.contract_id.new_id.partner_id.id
                vale['debit'] = obj.agency_num/obj.currency_id.rate_silent*obj.company_id.currency_id.rate_silent
                vale['credit'] = 0
                vale['name'] = u'汽车尾款'
                vale['date'] = invoice_obj_obj.date_invoice
                vale['analytic_account_id'] = obj.contract_id.analytic_id.id
                move_line_obj.create(cr, uid, vale)
                vale['amount_currency'] = -obj.agency_num
                vale['partner_id'] = obj.agent_id.id
                vale['debit'] = 0
                vale['credit'] = obj.agency_num/obj.currency_id.rate_silent*obj.company_id.currency_id.rate_silent
                vale['analytic_account_id'] = res_id
                move_line_obj.create(cr, uid, vale)
                self.action_invoice_create(cr, uid, ids, res_id, context=context)
                return self.write(cr, uid, ids, {'state':'margin','analytic_id':res_id})
        raise osv.except_osv(_('警告!'), _('对应的进口合同未签订！'))

    def btn_confirmed_sent(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.state == 'formulate':
            return self.write(cr, uid, ids, {'state':'confirmed'})
        if obj.state == 'signed':
            return self.write(cr, uid, ids, {'state':'formulate'})

    def purchase_confirm(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'formulate'})

    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'cancel'})

    def btn_message(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.state == 'draft':
            return self.write(cr, uid, ids, {'state':'confirmed'})
        if obj.state == 'formulate':
            return self.write(cr, uid, ids, {'state':'signed'})

    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        obj = self.browse(cr, uid, ids[0])
        if obj.state == 'draft':
            self.write(cr, uid, ids,{'state':'confirmed'})
        if obj.state == 'formulate':
            self.write(cr, uid, ids,{'state':'signed'})
        return self.pool['report'].get_action(cr, uid, ids, 'qdodoo_car_import_trade.report_qdodoo_entrusted_agency', context=context)

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        partner = self.pool.get('res.partner')
        if not partner_id:
            return {'value': {}}
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        if not company_id:
            raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
        supplier = partner.browse(cr, uid, partner_id, context=context)
        return {'value': {
            'pricelist_id': supplier.property_product_pricelist_purchase.id,
            }}

    # 计算车辆数量
    def _get_car_number(self):
        for ids in self:
            number = 0
            for line in ids.order_line:
                number += line.product_qty
            ids.car_number = number

    # 计算车辆价格
    def _get_car_money(self):
        for ids in self:
            number = 0
            for line in ids.order_line:
                number += line.price_unit*line.product_qty
            ids.car_money = number

    def wkf_send_rfq(self, cr, uid, ids, context=None):
        if not context:
            context= {}
        state = self.browse(cr, uid, ids[0]).state
        ir_model_data = self.pool.get('ir.model.data')
        template_id = False
        if context.get('agency_id', False):
            template_id = ir_model_data.get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'email_template_agency_id')[1]
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'qdodoo.entrusted.agency',
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

class mail_compose_message(models.Model):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get('default_model') == 'qdodoo.entrusted.agency' and context.get('default_res_id'):
            entrusted_obj = self.pool.get('qdodoo.entrusted.agency')
            context = dict(context, mail_post_autofollow=True)
            if context.get('default_state') == 'draft':
                entrusted_obj.write(cr, uid, context.get('default_res_id'),{'state':'confirmed'})
            if context.get('default_state') == 'formulate':
                entrusted_obj.write(cr, uid, context.get('default_res_id'),{'state':'signed'})
        return super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: