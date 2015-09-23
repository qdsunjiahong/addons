# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
from openerp.tools import float_compare
from openerp.tools.translate import _
from datetime import timedelta, datetime
from openerp.exceptions import except_orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
import logging
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class qdodoo_account_invoice_inherit(models.Model):
    _inherit = 'account.invoice'

    deposit_rate = fields.Float(u'定金比例(%)')

    def write(self, cr, uid, ids, value, context=None):
        obj = self.browse(cr, uid, ids[0])
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        contract_ids = contract_obj.search(cr, uid, [('name','=',obj.origin)])
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        agency_ids = agency_obj.search(cr, uid, [('name','=',obj.origin)])
        res_id = super(qdodoo_account_invoice_inherit, self).write(cr, uid, ids, value, context=context)
        obj_new = self.browse(cr, uid, ids[0])
        if obj_new.residual == 0 and value.get('state') == 'paid':
            if contract_ids:
                contract_obj_obj = contract_obj.browse(cr, uid, contract_ids[0])
                if contract_obj_obj.state == 'except_invoice':
                    contract_obj.write(cr, uid, [contract_ids[0]], {'state':'done'})
                else:
                    raise except_orm(_('警告!'), _('源进口合同未到结算阶段，不能完成发票.'))
            if agency_ids:
                agency_obj_obj = agency_obj.browse(cr, uid, agency_ids[0])
                if agency_obj_obj.state == 'import':
                    agency_obj.write(cr, uid, [agency_ids[0]], {'state':'done'})
                else:
                    raise except_orm(_('警告!'), _('源委托协议未到结算阶段，不能完成发票.'))
        return res_id

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_invoice_tax = self.env['account.invoice.tax']
        account_move = self.env['account.move']
        for inv in self:
            if not inv.journal_id.sequence_id:
                raise except_orm(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            date_invoice = inv.date_invoice

            company_currency = inv.company_id.currency_id
            # create the analytical lines, one move line per invoice line
            iml = inv._get_analytic_lines()
            # check if taxes are all computed
            compute_taxes = account_invoice_tax.compute(inv.with_context(lang=inv.partner_id.lang))
            inv.check_tax_lines(compute_taxes)

            # I disabled the check_total feature
            if self.env['res.users'].has_group('account.group_supplier_inv_check_total'):
                if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):
                    raise except_orm(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise except_orm(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += account_invoice_tax.move_line_get(inv.id)

            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
            else:
                ref = inv.number

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, ref, iml)

            name = inv.supplier_invoice_number or inv.name or '/'
            totlines = []
            if inv.payment_term:
                totlines = inv.with_context(ctx).payment_term.compute(total, date_invoice)[0]
            if totlines:
                res_amount_currency = total_currency
                ctx['date'] = date_invoice
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'ref': ref
                })

            date = date_invoice

            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            ref = inv.reference or inv.name
            contract_id = self.env['qdodoo.car.in.contract'].search([('name','=',ref)])
            if contract_id:
                for lines in iml:
                    lines['account_analytic_id'] = contract_id.analytic_id.id
            line = [(0, 0, self.line_get_convert(l, part.id, date)) for l in iml]
            line = inv.group_lines(iml, line)

            journal = inv.journal_id.with_context(ctx)
            if journal.centralisation:
                raise except_orm(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = inv.finalize_invoice_move_lines(line)

            move_vals = {
                'ref': inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal.id,
                'date': inv.date_invoice,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            ctx['company_id'] = inv.company_id.id
            period = inv.period_id
            if not period:
                period = period.with_context(ctx).find(date_invoice)[:1]
            if period:
                move_vals['period_id'] = period.id
                for i in line:
                    i[2]['period_id'] = period.id

            ctx['invoice'] = inv
            move = account_move.with_context(ctx).create(move_vals)
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'period_id': period.id,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
        self._log_event()
        return True

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')

        inv = self.browse(cr, uid, ids[0], context=context)
        if inv.deposit_rate:
            default_amount = inv.type in ('out_refund', 'in_refund') and -inv.residual*inv.deposit_rate/100 or inv.residual*inv.deposit_rate/100
        else:
            default_amount = inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual
        return {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                'default_amount': default_amount,
                'default_reference': inv.name,
                'close_after_process': True,
                'invoice_type': inv.type,
                'invoice_id': inv.id,
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
            }
        }

class qdodoo_purchase_order_inherit(models.Model):
    _inherit = 'purchase.order'

    is_type = fields.Selection([('purchase',u'采购订单'),('contract',u'进口合同')],u'类型')

    _defaults = {
        'is_type':'purchase',
    }

class qdodoo_pruchase_order_line_inherit(models.Model):
    _inherit = 'purchase.order.line'

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}

        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            if not uom_id:
                uom_id = self.default_get(cr, uid, ['product_uom'], context=context).get('product_uom', False)
                res['value']['product_uom'] = uom_id
            return res

        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')

        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:
            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if not name or not uom_id:
            # The 'or not uom_id' part of the above condition can be removed in master. See commit message of the rev. introducing this line.
            dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
            if product.description_purchase:
                name += '\n' + product.description_purchase
            res['value'].update({'name': name})

        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id

        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = product_uom_po_id

        res['value'].update({'product_uom': uom_id})

        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.datetime.now()


        supplierinfo = False
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.product_uom.id != uom_id:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
                min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
                    if qty:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                    qty = min_qty
        dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or 1.0
        res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})

        price = price_unit
        if price_unit is False or price_unit is None:
            # - determine price_unit and taxes_id
            if pricelist_id:
                date_order_str = datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                        product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
            else:
                price = product.standard_price

        taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
        taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
        price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, product.supplier_taxes_id, taxes_ids)
        res['value'].update({'price_unit': 0, 'taxes_id': taxes_ids})
        return res

class qdodoo_account_voucher_inherit(models.Model):
    _inherit = 'account.voucher'

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            local_context = dict(context, force_company=voucher.journal_id.company_id.id)
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher
            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context), local_context)
            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
            line_total = move_line_brw.debit - move_line_brw.credit
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, local_context)
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
            move_pool_obj = move_pool.browse(cr, uid, move_id, context=context)
            contract_obj = self.pool.get('qdodoo.car.in.contract')
            agency_obj = self.pool.get('qdodoo.car.in.contract')
            ref = move_pool_obj.ref
            contract_ids = contract_obj.search(cr, uid, [('name','=',ref)])
            agency_ids = agency_obj.search(cr, uid, [('name','=',ref)])
            analytic_account_id = ''
            if contract_ids:
                analytic_account_id = contract_obj.browse(cr, uid, contract_ids[0]).analytic_id.id
            if agency_ids:
                analytic_account_id = agency_obj.browse(cr, uid, agency_ids[0]).analytic_id.id
            for order_line in move_pool_obj.line_id:
                move_line_pool.write(cr, uid, order_line.id, {'analytic_account_id':analytic_account_id})
        return True

class qdodoo_payment_order_inherit(models.Model):
    _name = 'qdodoo.payment.order'
    _inherit = 'payment.order'
    _table = 'payment_order'

    contract_id = fields.Many2one('qdodoo.car.in.contract',u'关联合同')
    agency_id = fields.Many2one('qdodoo.entrusted.agency',u'委托代理')
    redeem_id = fields.Many2one('qdodoo.redeem.car',u'赎车')
    settlement_id = fields.Many2one('qdodoo.settlement.order',u'结算单')
    is_qdodoo = fields.Boolean(u'是否是通知单')

    _defaults = {
        'is_qdodoo':True,
    }

    def btn_select_order(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        move_lst = []
        for line in obj.line_ids:
            if line.move_line_id.invoice.id not in move_lst:
                move_lst.append(line.move_line_id.invoice.id)
        if obj.agency_id:
            invoice_obj = self.pool.get('account.invoice')
            invoice_ids = invoice_obj.search(cr, uid, [('origin','=',obj.agency_id.name)])
            move_lst += invoice_ids
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_tree')
        view_id = result and result[1] or False
        return {
              'name': ('发票'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'account.invoice',
              'type': 'ir.actions.act_window',
              'domain': [('id','in',move_lst)],
              'views': [(view_id,'tree'),(False,'form')],
              'view_id': [view_id],
              }

    def write(self, cr, uid, ids, vals, context=None):
        redeem_obj = self.pool.get('qdodoo.redeem.car')
        settlement_obj = self.pool.get('qdodoo.settlement.order')
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        move_line_obj = self.pool.get('account.move.line')
        move_obj = self.pool.get('account.move')
        invoice_obj = self.pool.get('account.invoice')
        obj = self.browse(cr, uid, ids[0])
        if vals.get('state') == 'done':
            if obj.contract_id:
                contract_obj.signal_workflow(cr, uid, [obj.contract_id.id], 'approved_except')
            if obj.agency_id:
                agency_obj.write(cr, uid, [obj.agency_id.id],{'state':'import'})
                move_ids = move_obj.search(cr, uid, [('ref','=',obj.agency_id.contract_id.name),('state','=','draft')])
                if move_ids:
                    invoice_ids = invoice_obj.search(cr, uid, [('origin','=',obj.agency_id.contract_id.name)])
                    invoice_obj_obj = invoice_obj.browse(cr, uid, invoice_ids[0])
                    debit = 0
                    for line in obj.agency_id.order_line:
                        debit += line.product_qty * line.price_unit * obj.agency_id.deposit_rate/100
                    val = {}
                    val['move_id'] = move_ids[0]
                    val['name'] = obj.agency_id.contract_id.name
                    val['ref'] = obj.agency_id.contract_id.name
                    val['journal_id'] = invoice_obj_obj.journal_id.id
                    val['period_id'] = invoice_obj_obj.period_id.id
                    val['account_id'] = invoice_obj_obj.account_id.id
                    val['debit'] = debit
                    val['credit'] = 0
                    val['quantity'] = 1
                    val['date'] = datetime.now().date()
                    val['analytic_account_id'] = obj.agency_id.analytic_id.id
                    # val['invoice'] = invoice_obj_obj.id
                    val['partner_id'] = obj.agency_id.agent_id.id
                    move_line_obj.create(cr, uid, val)
            if obj.redeem_id:
                redeem_obj.write(cr, uid, [obj.redeem_id.id],{'state':'done'})
            if obj.settlement_id:
                settlement_obj.write(cr, uid, [obj.settlement_id.id],{'state':'done'})
        if vals.get('state') == 'cancel':
            if obj.redeem_id:
                redeem_obj.write(cr, uid, [obj.redeem_id.id],{'state':'formulate'})
            if obj.settlement_id:
                settlement_obj.write(cr, uid, [obj.settlement_id.id],{'state':'formulate'})
            if obj.contract_id:
                contract_obj.write(cr, uid, [obj.contract_id.id],{'is_payment':False})
            if obj.agency_id:
                agency_obj.write(cr, uid, [obj.agency_id.id],{'is_payment':False})
        if vals.get('state') == 'open':
            if obj.redeem_id:
                redeem_obj.write(cr, uid, [obj.redeem_id.id],{'state':'signed'})
            if obj.settlement_id:
                settlement_obj.write(cr, uid, [obj.settlement_id.id],{'state':'signed'})
            if obj.contract_id:
                contract_obj.write(cr, uid, [obj.contract_id.id],{'is_payment':True})
            if obj.agency_id:
                agency_obj.write(cr, uid, [obj.agency_id.id],{'is_payment':True})
        return super(qdodoo_payment_order_inherit, self).write(cr, uid, ids, vals, context=context)

    @api.model
    def create(self, vals):
        vals['reference'] = self.env['ir.sequence'].get('qdodoo.payment.order')
        return super(qdodoo_payment_order_inherit, self).create(vals)

class qdodoo_car_in_contract(models.Model):
    """
        进口合同
    """
    _name = 'qdodoo.car.in.contract'    # 模型名称
    _inherit = 'purchase.order'
    _table = "purchase_order"

    STATE_SELECTION = [
        ('draft', u'草稿'),
        ('sent', u'询价'),
        ('confirmed', u'合同确认'),
        ('approved', u'支付定金'),
        ('lc', u'信用证'),
        ('customs', u'清关'),
        ('car', u'交车'),
        ('except_picking', u'委托协议'),
        ('in_ship', u'装船'),
        ('except_invoice', u'结算'),
        ('done', u'完成'),
        ('cancel', u'已取消')
    ]

    state = fields.Selection(STATE_SELECTION, u'状态', readonly=True,
                                  help="The status of the purchase order or the quotation request. "
                                       "A request for quotation is a purchase order in a 'Draft' status. "
                                       "Then the order has to be confirmed by the user, the status switch "
                                       "to 'Confirmed'. Then the supplier m"
                                       "ust confirm the order to change "
                                       "the status to 'Approved'. When the purchase order is paid and "
                                       "received, the status becomes 'Done'. If a cancel action occurs in "
                                       "the invoice or in the receipt of goods, the status becomes "
                                       "in exception.",
                                  select=True, copy=False)
    is_send = fields.Boolean(u'是否发送消息')
    contract_number = fields.Char(u'合同号')
    contract_date = fields.Date(u'合同日期')
    last_ship_date = fields.Date(u'最迟装船日期',required=True)
    car_number = fields.Float(u'车辆数',compute="_get_car_number")
    in_port = fields.Many2one('qdodoo.shipment.port',u'发货港',domain=[('type','=','in')],required=True)
    out_port = fields.Many2one('qdodoo.shipment.port',u'目的港',domain=[('type','=','out')],required=True)
    supplier_contract_version = fields.Many2one('qdodoo.contract.template',u'供应商合同版本',required=True)
    partial_shipment = fields.Selection([('ALLOWED','ALLOWED'),('NOT ALLOWED','NOT ALLOWED')],u'分批发运',required=True)
    trans_shipment = fields.Selection([('ALLOWED','ALLOWED'),('NOT ALLOWED','NOT ALLOWED')],u'转运',required=True)
    car_type = fields.Many2one('qdodoo.car.type',u'产品品类')
    payment_type = fields.Many2one('qdodoo.payment.type',u'付款方式')
    payment_line = fields.Many2one('qdodoo.payment.line',u'价格条款',required=True)
    contract_note = fields.Binary(u'上传合同')
    file_name = fields.Char(u'合同名称')
    deposit_rate = fields.Float(u'定金比例(%)')
    analytic_id = fields.Many2one('account.analytic.account',u'辅助核算项')
    agency_id = fields.Many2one('qdodoo.entrusted.agency',u'委托代理')
    is_payment = fields.Boolean(u'是否确认付款',copy=False)

    _defaults = {
        'is_send':False,
        'is_type':'contract',
        'is_payment':False,
    }

    def btn_bill(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_car_bill_lading')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_car_bill_lading')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('提单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.bill.lading',
              'type': 'ir.actions.act_window',
              'domain':[('contract_id','=',ids[0])],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    def action_invoice_create(self, cr, uid, ids, res_id=False, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        context = dict(context or {})

        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')

        res = False
        uid_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        for order in self.browse(cr, uid, ids, context=context):
            context.pop('force_company', None)
            if order.company_id.id != uid_company_id:
                #if the company of the document is different than the current user company, force the company in the context
                #then re-do a browse to read the property fields for the good company.
                context['force_company'] = order.company_id.id
                order = self.browse(cr, uid, order.id, context=context)

            # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
            inv_lines = []
            for po_line in order.order_line:
                if po_line.state == 'cancel':
                    continue
                acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
                inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                inv_line_data['account_analytic_id'] = res_id
                inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                inv_lines.append(inv_line_id)
                po_line.write({'invoice_lines': [(4, inv_line_id)]})

            # get invoice data and create invoice
            inv_data = self._prepare_invoice(cr, uid, order, inv_lines, context=context)
            inv_data['deposit_rate'] = order.deposit_rate
            inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            # compute the invoice
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            # Link this new invoice to related purchase order
            order.write({'invoice_ids': [(4, inv_id)]})
            res = inv_id
        return res

    def wkf_send_rfq(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        if not context:
            context= {}
        ir_model_data = self.pool.get('ir.model.data')
        try:
            if context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference(cr, uid, 'purchase', 'email_template_edi_purchase')[1]
            elif context.get('contract_id', False):
                template_id = ir_model_data.get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'email_template_in_car')[1]
            else:
                template_id = ir_model_data.get_object_reference(cr, uid, 'purchase', 'email_template_edi_purchase_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'qdodoo.car.in.contract',
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

    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'send_rfq')
        return self.pool['report'].get_action(cr, uid, ids, 'qdodoo_car_import_trade.report_qdodoo_car_import', context=context)

    def btn_rejected(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'confirmed'})

    def btn_redeem(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        lst_obj = []
        line_obj = self.pool.get('qdodoo.redeem.car.line')
        line_obj_ids = line_obj.search(cr, uid, [('agency_id','=',obj.agency_id.id)])
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
              'domain':[('contract_id','=',ids[0])],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    def btn_payment_order(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_settlement_order')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_settlement_order')
        view_id_form = result_form and result_form[1] or False
        agent_obj = self.pool.get('qdodoo.entrusted.agency')
        agent_ids = agent_obj.search(cr, uid, [('contract_id','=',ids[0])])
        return {
              'name': _('结算单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.settlement.order',
              'type': 'ir.actions.act_window',
              'domain':[('entrusted_id','in',agent_ids)],
              # 'context':{'contract_id':ids[0]},
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    def btn_entrust_agent(self, cr, uid, ids, context=None):
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        contract_line_obj = self.pool.get('purchase.order.line')
        agency_ids = agency_obj.search(cr, uid, [('contract_id','=',ids[0])])
        obj = self.browse(cr, uid, ids[0])
        if not agency_ids:
            val = {}
            val['pricelist_id'] = obj.pricelist_id.id
            val['contract_id'] = obj.id
            val['partner_id'] = obj.partner_id.id
            val['in_port'] = obj.in_port.id
            val['out_port'] = obj.out_port.id
            val['partial_shipment'] = obj.partial_shipment
            val['trans_shipment'] = obj.trans_shipment
            val['payment_type'] = obj.payment_type.id
            val['payment_line'] = obj.payment_line.id
            val['currency_id'] = obj.currency_id.id
            val['insurance_type'] = u'全险'
            res_id = agency_obj.create(cr, uid, val, context=context)
            order_line_new = obj.order_line.copy({'order_id':False,'entrusted_id':res_id})
            for order_line_id in order_line_new:
                contract_line_obj.write(cr, uid, order_line_id.id, {'price_unit':order_line_id.price_unit * ( 1- obj.deposit_rate/100)})
            agency_ids = []
            agency_ids.append(res_id)
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_entrusted_agency')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_entrusted_agency')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('委托协议'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.entrusted.agency',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',agency_ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    def btn_read_entrusted_agency(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_entrusted_agency')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_entrusted_agency')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('委托代理'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.entrusted.agency',
              'type': 'ir.actions.act_window',
              'domain':[('contract_id','in',ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    def btn_read_bill_lading(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_car_bill_lading')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_car_bill_lading')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('提单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.bill.lading',
              'type': 'ir.actions.act_window',
              'domain':[('contract_id','in',ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

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
              'domain':[('analytic_account_id','=',obj.analytic_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    def btn_payment_message(self, cr, uid, ids, context=None):
        payment_obj = self.pool.get('qdodoo.payment.order')
        payment_id = payment_obj.search(cr, uid, [('contract_id','=',ids[0])])
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
              'context':{'default_model':'contract_id'},
              'target':'new',
              }

    def _create_stock_moves(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Creates appropriate stock moves for given order lines, whose can optionally create a
        picking if none is given or no suitable is found, then confirms the moves, makes them
        available, and confirms the pickings.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise a standard
        incoming picking will be created to wrap the stock moves (default behavior of the stock.move)

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: purchase order to which the order lines belong
        :param list(browse_record) order_lines: purchase order line records for which picking
                                                and moves should be created.
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if omitted.
        :return: None
        """
        stock_move = self.pool.get('stock.move')
        todo_moves = []
        new_group = self.pool.get("procurement.group").create(cr, uid, {'name': order.name, 'partner_id': order.partner_id.id}, context=context)

        for order_line in order_lines:
            if order_line.state == 'cancel':
                continue
            if not order_line.product_id:
                continue

            if order_line.product_id.type in ('product', 'consu'):
                for vals in self._prepare_order_line_move(cr, uid, order, order_line, picking_id, new_group, context=context):
                    move = stock_move.create(cr, uid, vals, context=context)
                    todo_moves.append(move)

        todo_moves = stock_move.action_confirm(cr, uid, todo_moves)
        stock_move.force_assign(cr, uid, todo_moves)

    def action_picking_create(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids):
            picking_vals = {
                'picking_type_id': order.picking_type_id.id,
                'partner_id': order.partner_id.id,
                'date': order.date_order,
                'origin': order.name,
                'contract_id':order.id
            }
            picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
            self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)
        return picking_id

    def act_approved(self):
        if not self.contract_note:
            raise osv.except_osv(u'警告', "请先上传合同!")
        if self.deposit_rate < 0 or self.deposit_rate >=100:
            raise osv.except_osv(u'警告', "定金比例必须在0-100之间!")
        for line in self.order_line:
            if line.price_unit <= 0:
                raise osv.except_osv(u'警告', "货物明细中不能存在单价为0的数据!")
        if not self.is_payment:
            self.action_picking_create()
            location_model_cus, location_cus_ids = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'ir_cron_account_analytic_account')
            analytic_obj = self.env['account.analytic.account']
            val = {}
            val['name'] = self.name
            val['type'] = 'normal'
            val['parent_id'] = location_cus_ids
            res_id = analytic_obj.create(val)
            self.action_invoice_create(res_id.id)
            return self.write({'state':'approved','analytic_id':res_id.id})
        else:
            return self.write({'state':'approved'})

    def _get_car_number(self):
        for ids in self:
            number = 0
            for line in ids.order_line:
                number += line.product_qty
            ids.car_number = number

    def btn_message(self, cr, uid, ids, context=None):
        return self.signal_workflow(cr, uid, ids, 'send_rfq')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('qdodoo.car.in.contract')
        return super(qdodoo_car_in_contract, self).create(vals)

    def write(self, cr, uid, ids, value, context=None):
        if value.get('state') == 'sent':
            obj = self.browse(cr, uid, ids[0])
            line_obj = self.pool.get('purchase.order.line')
            for line in obj.order_line:
                line_obj.write(cr, uid, line.id, {'state':'confirmed'})
        return super(qdodoo_car_in_contract, self).write(cr, uid, ids, value, context=context)

class qdodoo_stock_picking_inherit(models.Model):
    _inherit = 'stock.picking'

    contract_id = fields.Many2one('qdodoo.car.in.contract',u'合同')

    @api.one
    def do_transfer(self):
        res = super(qdodoo_stock_picking_inherit, self).do_transfer()
        if self.contract_id:
            lading_obj = self.env['qdodoo.car.bill.lading']
            res_id = lading_obj.create({'contract_id':self.contract_id.id,'in_port':self.contract_id.in_port.id,'out_port':self.contract_id.out_port.id,
                               'partner_id':self.contract_id.partner_id.id,'in_partner_id':self.contract_id.agency_id.agent_id.id,
                               })
            archives_obj = self.env['qdodoo.car.archives']
            for line in self.pack_operation_ids:
                for i in range(int(line.product_qty)):
                    payment_ids = self.env['qdodoo.payment.order'].search([('agency_id','=',self.contract_id.agency_id.id)])
                    price_unit = self.get_import_price(self.contract_id.id).get(line.product_id.id)*(1-self.contract_id.deposit_rate/100)*self.contract_id.agency_id.deposit_rate/100
                    payment_line_ids = self.env['payment.line'].search([('order_id','=',payment_ids[0].id),('amount_currency','=',price_unit),('state','!=','cancel')])
                    payment_line_id = payment_line_ids and payment_line_ids[0].id or ''

                    archives_obj.create({'lading_number':res_id.id,'car_model':line.product_id.id,'contract_id':self.contract_id.id,
                                         'import_number':self.contract_id.contract_number,'agency_id':self.contract_id.agency_id.id,
                                         'car_sale_price':self.get_import_price(self.contract_id.id).get(line.product_id.id),'import_pay_money':self.get_import_price(self.contract_id.id).get(line.product_id.id)*self.contract_id.deposit_rate/100,
                                         'credit_price':self.get_import_price(self.contract_id.id).get(line.product_id.id)*(1-self.contract_id.deposit_rate/100),'agent_margin_price':self.get_import_price(self.contract_id.id).get(line.product_id.id)*(1-self.contract_id.deposit_rate/100)*self.contract_id.agency_id.deposit_rate/100,
                                         'payment_id':payment_line_id})
        return res

    # 获取{产品id：进口价}
    def get_import_price(self, cr, uid, ids, contract_id, context=None):
        valu = {}
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        for contract_obj_ids in contract_obj.browse(cr, uid, contract_id):
            for contract_obj_id in contract_obj_ids.order_line:
                valu[contract_obj_id.product_id.id] = contract_obj_id.price_subtotal
        return valu

class qdodoo_mail_compose_message_inherit(models.Model):
    _inherit = ['mail.compose.message']
    def send_mail(self, cr, uid, ids, context=None):
        if context.get('is_contract'):
            obj = self.pool.get('qdodoo.car.in.contract')
            obj.signal_workflow(cr, uid, context.get('active_ids'), 'send_rfq')
        if context.get('agency_id'):
            obj = self.pool.get('qdodoo.entrusted.agency')
            obj.write(cr, uid, context.get('active_ids'), {'state':'confirmed'})
        if context.get('redeem_id'):
            obj = self.pool.get('qdodoo.redeem.car')
            obj.write(cr, uid, context.get('active_ids'), {'state':'confirmed'})
        return super(qdodoo_mail_compose_message_inherit, self).send_mail(cr, uid, ids, context=context)

class qdodoo_payment_model(models.Model):
    """
        选择付款方式
    """
    _name = 'qdodoo.payment.model'    # 模型名称

    name = fields.Many2one('payment.mode',u'付款方式',required=True)

    def search_date(self, cr, uid, ids,context=None):
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        redeem_obj = self.pool.get('qdodoo.redeem.car')
        settlement_obj = self.pool.get('qdodoo.settlement.order')
        payment_obj = self.pool.get('qdodoo.payment.order')
        payment_line_obj = self.pool.get('payment.line')
        account_obj = self.pool.get('account.invoice')
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
        view_id_form = result_form and result_form[1] or False
        vals = {}
        if context.get('default_model') == 'contract_id':
            obj = contract_obj.browse(cr, uid, context.get('active_id'))
            vals['payment_supplier'] = obj.partner_id.id
        if context.get('default_model') == 'agency_id':
            obj = agency_obj.browse(cr, uid, context.get('active_id'))
            vals['payment_supplier'] = obj.agent_id.id
            vals['user_id'] = uid
            vals['mode'] = context.get('name')
            vals['date_prefered'] = 'due'
            vals[context.get('default_model')] = obj.id
            res_id = payment_obj.create(cr, uid, vals, context=context)
            for line in obj.order_line:
                val = {}
                val['order_id'] = res_id
                val['date'] = datetime.now().date()
                val['partner_id'] = obj.agent_id.id
                val['amount_currency'] = line.product_qty * line.price_unit * obj.deposit_rate / 100
                val['communication'] = obj.name
                val['name'] = obj.pool.get('ir.sequence').get(cr, uid, 'payment.line')
                val['state'] = 'normal'
                val['currency'] = obj.currency_id.id
                payment_line_obj.create(cr, uid, val, context=context)
            payment_line_obj.create(cr, uid, {
                'order_id':res_id,
                'date':datetime.now().date(),
                'partner_id':obj.agent_id.id,
                'amount_currency':float(obj.agency_fee)*obj.car_number,
                'communication':obj.name,
                'name':obj.pool.get('ir.sequence').get(cr, uid, 'payment.line'),
                'state':'normal',
                # 'currency':obj.currency_id.id,
            }, context=context)
            return {
              'name': _('付款通知'),
              'view_type': 'form',
              "view_mode": 'form,tree',
              'res_model': 'qdodoo.payment.order',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',res_id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id_form],
              }
        if context.get('default_model') == 'redeem_id':
            obj = redeem_obj.browse(cr, uid, context.get('active_id'))
            vals['payment_supplier'] = obj.partner_id.id
        if context.get('default_model') == 'settlement_id':
            obj = settlement_obj.browse(cr, uid, context.get('active_id'))
            vals['payment_supplier'] = obj.partner_id.id
        vals['user_id'] = uid
        vals['mode'] = context.get('name')
        vals['date_prefered'] = 'due'
        vals[context.get('default_model')] = obj.id
        res_id = payment_obj.create(cr, uid, vals, context=context)
        account_id = account_obj.search(cr, uid, [('origin','=',obj.name),('state','!=','paid')])
        if account_id:
            account_obj.signal_workflow(cr, uid, [account_id[0]], 'invoice_open')
            account_id_obj = account_obj.browse(cr, uid, account_id[0])
            move_line_id = ''
            for line in account_id_obj.move_id.line_id:
                if line.account_id.type == 'payable':
                    move_line_id = line.id
            for line in account_id_obj.invoice_line:
                val = {}
                val['order_id'] = res_id
                val['date'] = datetime.now().date()
                val['move_line_id'] = move_line_id
                val['partner_id'] = account_id_obj.partner_id.id
                val['amount_currency'] = line.price_subtotal * obj.deposit_rate / 100
                if context.get('default_model') == 'contract_id':
                    val['currency'] = obj.currency_id.id
                val['communication'] = account_id_obj.name
                val['name'] = obj.pool.get('ir.sequence').get(cr, uid, 'payment.line')
                val['state'] = 'normal'
                payment_line_obj.create(cr, uid, val, context=None)
        return {
          'name': _('付款通知'),
          'view_type': 'form',
          "view_mode": 'form,tree',
          'res_model': 'qdodoo.payment.order',
          'type': 'ir.actions.act_window',
          'domain':[('id','=',res_id)],
          'views': [(view_id,'tree'),(view_id_form,'form')],
          'view_id': [view_id_form],
          }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: