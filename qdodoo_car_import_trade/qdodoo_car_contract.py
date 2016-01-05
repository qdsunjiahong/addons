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
import time
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class qdodoo_account_invoice_inherit(models.Model):
    _inherit = 'account.invoice'

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
            # 获取明细中的分析账户
            account_analytic_id = 0
            for line_key in inv.invoice_line:
                if line_key.account_analytic_id:
                    account_analytic_id = line_key.account_analytic_id.id
            contract_id = self.env['qdodoo.car.in.contract'].search([('name','=',ref)])
            contract_id_new = self.env['qdodoo.entrusted.agency'].search([('name','=',ref)])
            contract = contract_id if contract_id else (contract_id_new if contract_id_new else False)
            if account_analytic_id:
                for lines in iml:
                        lines['account_analytic_id'] = account_analytic_id
            else:
                if contract:
                    for lines in iml:
                        lines['account_analytic_id'] = contract.analytic_id.id
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

class qdodoo_purchase_order_inherit(models.Model):
    _inherit = 'purchase.order'

    is_type = fields.Selection([('purchase',u'采购订单'),('contract',u'整车采购'),('contract_new',u'进口合同')],u'类型')
    contract_id_three = fields.Many2one('qdodoo.car.in.contract',u'整车采购')

    _defaults = {
        'is_type':'purchase',
    }

    def create(self, cr, uid, values, context=None):
        if context.get('contract_id_three'):
            values['contract_id_three'] = context.get('contract_id_three')
        return super(qdodoo_purchase_order_inherit, self).create(cr, uid, values, context=context)

class qdodoo_pruchase_order_line_inherit(models.Model):
    _inherit = 'purchase.order.line'

    # year_id = fields.Many2one('qdodoo.product.year',u'年款')
    # brand_id = fields.Many2one('qdodoo.product.brand',u'品牌')
    # series_id = fields.Many2one('qdodoo.series.of',u'系列')
    # model_id = fields.Many2one('qdodoo.model',u'型号')
    # version_id = fields.Many2one('qdodoo.version',u'版本')
    # appearance_id = fields.Many2one('qdodoo.appearance',u'外观')
    # interior_id = fields.Many2one('qdodoo.interior',u'内饰')
    # configuration_id = fields.Many2one('qdodoo.configuration',u'配置')
    order_id = fields.Many2one('purchase.order', 'Order Reference',required=False, select=True, ondelete='cascade')

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
        # price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, product.supplier_taxes_id, taxes_ids)
        res['value'].update({'price_unit': 0, 'taxes_id': taxes_ids})
        return res

    # 自动生成辅助核算项
    def create(self, cr, uid, vals, context=None):
        if vals.get('order_id'):
            purchase_obj = self.pool.get('purchase.order').browse(cr, uid, vals.get('order_id'))
            if purchase_obj.contract_id_three:
                if purchase_obj.contract_id_three.purchase_type == 'agency_in':
                    agency_obj = self.pool.get('qdodoo.entrusted.agency')
                    agency_ids = agency_obj.search(cr, uid, [('contract_id','=',purchase_obj.contract_id_three.id),('margin_log','=',False)])
                    agency_ids_obj = agency_obj.browse(cr, uid, agency_ids)
                    vals['account_analytic_id'] = agency_ids_obj.analytic_id.id
                if purchase_obj.contract_id_three.purchase_type == 'own_in':
                    vals['account_analytic_id'] = purchase_obj.contract_id_three.new_id.analytic_id.id
        return super(qdodoo_pruchase_order_line_inherit, self).create(cr, uid, vals, context=context)

class qdodoo_account_voucher_inherit(models.Model):
    _inherit = 'account.voucher'

    invoice_id_new = fields.Many2one('account.invoice',u'发票')
    analytic_obj = fields.Many2one('account.analytic.account',u'辅助核算项')
    is_close = fields.Boolean(u'是否关闭辅助核算项')

    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, analytic_obj=False, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({'date': date})
        #read the voucher rate with the right date in the context
        currency_id = currency_id or self.pool.get('res.company').browse(cr, uid, company_id, context=ctx).currency_id.id
        voucher_rate = self.pool.get('res.currency').read(cr, uid, [currency_id], ['rate'], context=ctx)[0]['rate']
        ctx.update({
            'voucher_special_currency': payment_rate_currency_id,
            'voucher_special_currency_rate': rate * voucher_rate})
        res = self.recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, analytic_obj, context=ctx)
        vals = self.onchange_rate(cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
        for key in vals.keys():
            res[key].update(vals[key])
        return res

    def write(self, cr, uid, ids, valu, context=None):
        super(qdodoo_account_voucher_inherit, self).write(cr, uid, ids, valu, context=context)
        obj = self.browse(cr, uid, ids[0])
        analytic_obj = self.pool.get('account.analytic.account')
        if obj.analytic_obj and valu.get('state') == 'posted' and obj.is_close:
            analytic_obj.write(cr, uid, obj.analytic_obj.id, {'log':True})
        return True

    def button_proforma_voucher(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'invoice_id_new':context.get('active_id')})
        return super(qdodoo_account_voucher_inherit, self).button_proforma_voucher(cr, uid, ids, context=context)

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
            invoice_obj = self.pool.get('account.invoice')
            ref = move_pool_obj.ref
            contract_ids = contract_obj.search(cr, uid, [('name','=',ref)])
            agency_ids = agency_obj.search(cr, uid, [('name','=',ref)])
            analytic_account_id = ''
            if contract_ids:
                analytic_account_id = contract_obj.browse(cr, uid, contract_ids[0]).analytic_id.id
            if agency_ids:
                analytic_account_id = agency_obj.browse(cr, uid, agency_ids[0]).analytic_id.id

            invoice_obj_obj = invoice_obj.browse(cr, uid, voucher.invoice_id_new.id)
            for line_key in invoice_obj_obj.invoice_line:
                if line_key.account_analytic_id:
                    analytic_account_id = line_key.account_analytic_id.id
            if not analytic_account_id:
                analytic_account_id = voucher.analytic_obj.id
            for order_line in move_pool_obj.line_id:
                if voucher.name:
                    move_line_pool.write(cr, uid, order_line.id, {'analytic_account_id':analytic_account_id,'name':voucher.name})
                else:
                    move_line_pool.write(cr, uid, order_line.id, {'analytic_account_id':analytic_account_id})
        return True

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, analytic_obj=False, context=None):
        if context is None:
            context = {}
        if not journal_id:
            return False
        journal_pool = self.pool.get('account.journal')
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        if ttype in ('sale', 'receipt'):
            account_id = journal.default_debit_account_id
        elif ttype in ('purchase', 'payment'):
            account_id = journal.default_credit_account_id
        else:
            account_id = journal.default_credit_account_id or journal.default_debit_account_id
        tax_id = False
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id

        vals = {'value':{} }
        if ttype in ('sale', 'purchase'):
            vals = self.onchange_price(cr, uid, ids, line_ids, tax_id, partner_id, context)
            vals['value'].update({'tax_id':tax_id,'amount': amount})
        currency_id = False
        if journal.currency:
            currency_id = journal.currency.id
        else:
            currency_id = journal.company_id.currency_id.id

        period_ids = self.pool['account.period'].find(cr, uid, dt=date, context=dict(context, company_id=company_id))
        vals['value'].update({
            'currency_id': currency_id,
            'payment_rate_currency_id': currency_id,
            'period_id': period_ids and period_ids[0] or False
        })
        #in case we want to register the payment directly from an invoice, it's confusing to allow to switch the journal
        #without seeing that the amount is expressed in the journal currency, and not in the invoice currency. So to avoid
        #this common mistake, we simply reset the amount to 0 if the currency is not the invoice currency.
        if context.get('payment_expected_currency') and currency_id != context.get('payment_expected_currency'):
            vals['value']['amount'] = 0
            amount = 0
        if partner_id:
            res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date,analytic_obj, context)
            for key in res.keys():
                vals[key].update(res[key])
        return vals

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, analytic_obj=False, context=None):
        if not journal_id:
            return {}
        if context is None:
            context = {}
        #TODO: comment me and use me directly in the sales/purchases views
        res = self.basic_onchange_partner(cr, uid, ids, partner_id, journal_id, ttype, context=context)
        if ttype in ['sale', 'purchase']:
            return res
        ctx = context.copy()
        # not passing the payment_rate currency and the payment_rate in the context but it's ok because they are reset in recompute_payment_rate
        ctx.update({'date': date})
        vals = self.recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, analytic_obj,context=ctx)
        vals2 = self.recompute_payment_rate(cr, uid, ids, vals, currency_id, date, ttype, journal_id, amount, context=context)
        for key in vals.keys():
            res[key].update(vals[key])
        for key in vals2.keys():
            res[key].update(vals2[key])
        #TODO: can probably be removed now
        #TODO: onchange_partner_id() should not returns [pre_line, line_dr_ids, payment_rate...] for type sale, and not
        # [pre_line, line_cr_ids, payment_rate...] for type purchase.
        # We should definitively split account.voucher object in two and make distinct on_change functions. In the
        # meanwhile, bellow lines must be there because the fields aren't present in the view, what crashes if the
        # onchange returns a value for them
        if ttype == 'sale':
            del(res['value']['line_dr_ids'])
            del(res['value']['pre_line'])
            del(res['value']['payment_rate'])
        elif ttype == 'purchase':
            del(res['value']['line_cr_ids'])
            del(res['value']['pre_line'])
            del(res['value']['payment_rate'])
        return res

    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, analytic_obj=False, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')

        #set default values
        default = {
            'value': {'line_dr_ids': [], 'line_cr_ids': [], 'pre_line': False},
        }

        # drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])])
        for line in line_pool.browse(cr, uid, line_ids, context=context):
            if line.type == 'cr':
                default['value']['line_cr_ids'].append((2, line.id))
            else:
                default['value']['line_dr_ids'].append((2, line.id))

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id

        total_credit = 0.0
        total_debit = 0.0
        account_type = None
        if context.get('account_id'):
            account_type = self.pool['account.account'].browse(cr, uid, context['account_id'], context=context).type
        if ttype == 'payment':
            if not account_type:
                account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            if not account_type:
                account_type = 'receivable'

        if not context.get('move_line_ids', False):
            if analytic_obj and type(analytic_obj) == int:
                ids = move_line_pool.search(cr, uid, [('analytic_account_id','=',analytic_obj),('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
            else:
                ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_lines_found = []

        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_lines_found.append(line.id)
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_lines_found.append(line.id)
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_lines_found.append(line.id)
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        remaining_amount = price
        #voucher line creation
        for line in account_move_lines:

            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (line.id in move_lines_found) and min(abs(remaining_amount), amount_unreconciled) or 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            remaining_amount -= rs['amount']
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            if not move_lines_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        rs['amount'] = amount
                        total_debit -= amount
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
        return default

class qdodoo_account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    log = fields.Boolean(u'是否关闭')

    _defaults = {
        'log':False,
    }

class qdodoo_payment_order_inherit(models.Model):
    _name = 'qdodoo.payment.order'
    _inherit = 'payment.order'
    _table = 'payment_order'

    mode = fields.Many2one('payment.mode', u'付款方式', select=True, required=False)
    contract_id = fields.Many2one('qdodoo.car.in.contract',u'关联整车采购')
    contract_new_id = fields.Many2one('qdodoo.car.in.contract.new',u'关联合同')
    agency_id = fields.Many2one('qdodoo.entrusted.agency',u'委托代理')
    redeem_id = fields.Many2one('qdodoo.redeem.car',u'赎车')
    # settlement_id = fields.Many2one('qdodoo.settlement.order',u'结算单')
    is_qdodoo = fields.Boolean(u'是否是通知单')
    pay_type = fields.Selection([('in',u'收款'),('out',u'付款')],u'收付款类型')
    partner_qdodoo_id = fields.Many2one('res.partner',u'业务伙伴')
    application_date = fields.Datetime(u'申请日期')
    state = fields.Selection([
            ('draft', u'草稿'),
            ('cancel', u'取消'),
            ('confirmed', u'确认'),
            ('open', u'审批'),
            ('pay', u'付款'),
            ('done', u'完成')], u'状态', select=True, copy=False)

    _defaults = {
        'is_qdodoo':True,
        'date_prefered':'now',
        'pay_type':'out'
    }

    # 驳回
    def btn_cancel(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.state == 'confirmed':
            return self.write(cr, uid, ids, {'state':'draft'})
        if obj.state == 'open':
            return self.write(cr, uid, ids, {'state':'confirmed'})
        if obj.state == 'pay':
            return self.write(cr, uid, ids, {'state':'open'})

    # 批准付款
    def btn_confirm_new(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'pay'})

    # 确认
    def btn_confirm(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.pay_type == 'in':
            return self.write(cr, uid, ids, {'state':'pay'})
        return self.write(cr, uid, ids, {'state':'open'})

    # 完成付款
    def btn_pay_end(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        account_obj = self.pool.get('account.invoice')
        for line in obj.line_ids:
            if line.invoice_id and line.invoice_id.state == 'draft':
                account_obj.signal_workflow(cr, uid, [line.invoice_id.id], 'invoice_open')
        self.action_open(cr, uid, ids)
        return self.write(cr, uid, ids, {'state':'done'})

    # 取消
    def cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'cancel'})

    # 提交申请
    def btn_appliy(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'confirmed','application_date':datetime.now()})

    # 查看关联发票
    def btn_select_order(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        move_lst = []
        for line in obj.line_ids:
            if line.invoice_id.id not in move_lst:
                move_lst.append(line.invoice_id.id)
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

    # 根据时间获取对应会计区间
    def get_period_id(self, cr, uid, ids, date, context=None):
        period_obj = self.pool.get('account.period')
        period_ids = period_obj.search(cr, uid, [('date_start','<=',date),('date_stop','>=',date),('special','=',False)])
        if not period_ids:
            raise osv.except_osv(_('错误!'), _('缺少正在使用的会计区间！'))
        return period_ids[0]

    # 付款通知单完成时
    def write(self, cr, uid, ids, vals, context=None):
        redeem_obj = self.pool.get('qdodoo.redeem.car')
        # settlement_obj = self.pool.get('qdodoo.settlement.order')
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        contract_new_obj = self.pool.get('qdodoo.car.in.contract.new')
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        move_line_obj = self.pool.get('account.move.line')
        move_obj = self.pool.get('account.move')
        account_obj = self.pool.get('account.account')
        invoice_obj = self.pool.get('account.invoice')
        obj = self.browse(cr, uid, ids[0])
        if vals.get('state') == 'done':
            if obj.contract_id:
                contract_obj.write(cr, uid, [obj.contract_id.id], {'state':'customs'})
            if obj.contract_new_id:
                # 支付履约保证金()
                if obj.contract_new_id.deposit_margin and obj.contract_new_id.deposit_amount:
                    # 获取应付账款科目
                    account_ids = account_obj.search(cr, uid, [('type','=','receivable')],order='id')
                    invoice_obj_obj = obj.contract_new_id.old_id.invoice_id
                    obj_sequence = self.pool.get('ir.sequence')
                    c = {'fiscalyear_id': invoice_obj_obj.period_id.fiscalyear_id.id}
                    new_name = obj_sequence.next_by_id(cr, uid, invoice_obj_obj.journal_id.sequence_id.id, c)
                    # 创建分录
                    value = {}
                    value['journal_id'] = obj.mode.journal.id
                    value['period_id'] = self.get_period_id(cr, uid, ids, invoice_obj_obj.date_invoice)
                    value['ref'] = obj.contract_new_id.name
                    value['date'] = datetime.now().date()
                    value['name'] = new_name
                    res_move_id = move_obj.create(cr, uid, value)
                    vale = {}
                    vale['move_id'] = res_move_id
                    vale['name'] = '履约保证金'
                    vale['ref'] = '履约保证金'
                    vale['journal_id'] = obj.mode.journal.id
                    vale['period_id'] = self.get_period_id(cr, uid, ids, invoice_obj_obj.date_invoice)
                    vale['account_id'] = invoice_obj_obj.account_id.id
                    vale['quantity'] = 1
                    vale['date'] = invoice_obj_obj.date_invoice
                    vale['invoice'] = invoice_obj_obj.id
                    vale['debit'] = obj.contract_new_id.deposit_amount/obj.contract_new_id.currency_id.rate_silent*obj.contract_new_id.company_id.currency_id.rate_silent
                    vale['amount_currency'] = obj.contract_new_id.deposit_amount
                    vale['credit'] = 0
                    vale['analytic_account_id'] = obj.contract_new_id.analytic_id.id
                    vale['partner_id'] = obj.contract_new_id.partner_id.id
                    move_line_obj.create(cr, uid, vale)
                    vale['debit'] = 0
                    vale['credit'] = obj.contract_new_id.deposit_amount/obj.contract_new_id.currency_id.rate_silent*obj.contract_new_id.company_id.currency_id.rate_silent
                    vale['amount_currency'] = -obj.contract_new_id.deposit_amount
                    vale['account_id'] = invoice_obj_obj.account_id.id
                    move_line_obj.create(cr, uid, vale)
                contract_new_obj.write(cr, uid, obj.contract_new_id.id, {'state':'except_picking'})
            if obj.agency_id:
                res_num = self.search(cr, uid, [('agency_id','=',obj.agency_id.id),('state','not in',('done','cancel'))])
                res_num.remove(ids[0])
                if not res_num:
                    agency_obj.write(cr, uid, [obj.agency_id.id],{'state':'import'})
                log = 0
                for line in obj.line_ids:
                    if line.invoice_id:
                        log = 1
                if not log:
                    # 查询委托协议对应的发票信息
                    invoice_ids = invoice_obj.search(cr, uid, [('origin','=',obj.agency_id.name)])
                    invoice_obj_obj = invoice_obj.browse(cr, uid, invoice_ids[0])
                    obj_sequence = self.pool.get('ir.sequence')
                    c = {'fiscalyear_id': invoice_obj_obj.period_id.fiscalyear_id.id}
                    new_name = obj_sequence.next_by_id(cr, uid, invoice_obj_obj.journal_id.sequence_id.id, c)
                    # 创建分录
                    value = {}
                    value['journal_id'] = obj.mode.journal.id
                    value['period_id'] = self.get_period_id(cr, uid, ids, invoice_obj_obj.date_invoice)
                    value['ref'] = obj.agency_id.name
                    value['date'] = datetime.now().date()
                    value['name'] = new_name
                    res_move_id = move_obj.create(cr, uid, value)
                    vale = {}
                    vale['move_id'] = res_move_id
                    vale['name'] = '委托协议定金'
                    vale['ref'] = '委托协议定金'
                    vale['journal_id'] = obj.mode.journal.id
                    vale['period_id'] = self.get_period_id(cr, uid, ids, invoice_obj_obj.date_invoice)
                    vale['account_id'] = invoice_obj_obj.account_id.id
                    vale['quantity'] = 1
                    vale['date'] = invoice_obj_obj.date_invoice
                    vale['invoice'] = invoice_obj_obj.id
                    vale['debit'] = obj.agency_id.margin_rate_money
                    vale['credit'] = 0
                    vale['analytic_account_id'] = obj.agency_id.analytic_id.id
                    vale['partner_id'] = obj.agency_id.agent_id.id
                    move_line_obj.create(cr, uid, vale)
                    vale['debit'] = 0
                    vale['credit'] = obj.agency_id.margin_rate_money
                    vale['account_id'] = obj.mode.journal.default_credit_account_id.id
                    move_line_obj.create(cr, uid, vale)
            if obj.redeem_id:
                redeem_obj.write(cr, uid, [obj.redeem_id.id],{'state':'done'})
                # 获取源单据
                origin = ''
                for line_key in obj.line_ids:
                    if line_key.communication:
                        origin = line_key.communication
                # 获取对应的发票
                if origin:
                    # 获取对应的委托协议的辅助核算项
                    agency_id = agency_obj.search(cr, uid, [('name','=',origin)])
                    analytic_id = agency_obj.browse(cr, uid, agency_id[0]).analytic_id.id
                    invoice_ids = invoice_obj.search(cr, uid, [('origin','=',origin)])
                    invoice_obj_obj = invoice_obj.browse(cr, uid, invoice_ids[0])
                    obj_sequence = self.pool.get('ir.sequence')
                    c = {'fiscalyear_id': invoice_obj_obj.period_id.fiscalyear_id.id}
                    new_name = obj_sequence.next_by_id(cr, uid, invoice_obj_obj.journal_id.sequence_id.id, c)
                    # 创建分录
                    value = {}
                    value['journal_id'] = obj.mode.journal.id
                    value['period_id'] = self.get_period_id(cr, uid, ids, invoice_obj_obj.date_invoice)
                    value['ref'] = obj.contract_id.new_id.name
                    value['date'] = datetime.now().date()
                    res_move_id = move_obj.create(cr, uid, value)
                    vale = {}
                    vale['move_id'] = res_move_id
                    vale['name'] = obj.redeem_id.name
                    vale['ref'] = '赎车款'
                    vale['name'] = '赎车款'
                    vale['journal_id'] = obj.mode.journal.id
                    vale['period_id'] = self.get_period_id(cr, uid, ids, invoice_obj_obj.date_invoice)
                    vale['account_id'] = invoice_obj_obj.account_id.id
                    vale['quantity'] = 1
                    vale['date'] = invoice_obj_obj.date_invoice
                    vale['invoice'] = invoice_obj_obj.id
                    vale['debit'] = obj.total
                    vale['credit'] = 0
                    vale['analytic_account_id'] = analytic_id
                    vale['partner_id'] = obj.partner_qdodoo_id.id
                    move_line_obj.create(cr, uid, vale)
                    vale['debit'] = 0
                    vale['credit'] = obj.total
                    vale['account_id'] = obj.mode.journal.default_credit_account_id.id
                    move_line_obj.create(cr, uid, vale)
        return super(qdodoo_payment_order_inherit, self).write(cr, uid, ids, vals, context=context)

    @api.model
    def create(self, vals):
        vals['reference'] = self.env['ir.sequence'].get('qdodoo.payment.order')
        return super(qdodoo_payment_order_inherit, self).create(vals)

class qdodoo_payment_line_inherit(models.Model):
    _inherit = 'payment.line'

    invoice_id = fields.Many2one('account.invoice',u'发票')

class qdodoo_car_in_contract(models.Model):
    """
        整车进口
    """
    _name = 'qdodoo.car.in.contract'    # 模型名称
    _inherit = 'purchase.order'
    _table = "purchase_order"

    STATE_SELECTION = [
        ('draft', u'草稿'),
        ('sent', u'询价'),
        ('confirmed', u'订单确认'),
        ('approved', u'进口合同'),
        ('except_picking', u'委托协议'),
        ('lc', u'支付货款'),
        ('customs', u'收货通知'),
        ('customs_dec', u'报关报检'),
        ('picking_sale', u'仓储'),
        ('car', u'赎车'),
        ('in_ship', u'提车'),
        ('except_invoice', u'结算'),
        # ('no_money', u'核销'),
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
    contract_number = fields.Char(u'进口合同号')
    contract_date = fields.Date(u'合同日期')
    last_ship_date = fields.Date(u'最迟发运日期',required=True)
    car_number = fields.Float(u'车辆数',compute="_get_car_number")
    in_port = fields.Many2one('qdodoo.shipment.port',u'发货港',domain=[('type','=','in')])
    out_port = fields.Many2one('qdodoo.shipment.port',u'目的港',domain=[('type','=','out')],required=True)
    supplier_contract_version = fields.Many2one('qdodoo.contract.template',u'供应商合同版本',required=True)
    partial_shipment = fields.Selection([('ALLOWED','ALLOWED'),('NOT ALLOWED','NOT ALLOWED')],u'分批发运')
    trans_shipment = fields.Selection([('ALLOWED','ALLOWED'),('NOT ALLOWED','NOT ALLOWED')],u'转运')
    car_type = fields.Many2one('qdodoo.car.type',u'产品品类')
    payment_type = fields.Many2one('qdodoo.payment.type',u'付款方式')
    payment_line = fields.Many2one('qdodoo.payment.line',u'价格条款',required=True)
    contract_note = fields.Binary(u'合同原件')
    file_name = fields.Char(u'合同名称')
    deposit_rate = fields.Float(u'定金比例(%)')
    analytic_id = fields.Many2one('account.analytic.account',u'辅助核算项',copy=False)
    agency_id = fields.Many2one('qdodoo.entrusted.agency',u'委托代理')
    is_payment = fields.Boolean(u'是否确认付款',copy=False)
    customer_id = fields.Many2one('res.partner',u'收货人')
    receive_id = fields.Many2one('res.partner',u'买方')
    purchase_type = fields.Selection([('agency_in',u'委托进口'),('own_in',u'自营进口'),('own',u'内贸自营采购')],u'采购渠道',copy=False)
    contract_type = fields.Selection([('in',u'内贸'),('out',u'进口')],u'采购渠道')
    deposit_amount = fields.Float(u'定金金额')
    deposit_margin = fields.Boolean(u'定金既履约保证金',copy=False)
    deposit_margin_customer = fields.Many2one('res.partner',u'履约保证金受托方')
    new_id = fields.Many2one('qdodoo.car.in.contract.new',u'进口合同',copy=False)
    invoice_id = fields.Many2one('account.invoice',u'发票',copy=False)
    new_pay = fields.Boolean(u'定金/保证金委托支付',copy=False)

    # 获取当前登录用户的公司对应的客户
    def get_customer_id(self, cr, uid, ids, context=None):
        obj = self.pool.get('res.users')
        return obj.browse(cr, uid, uid).company_id.partner_id.id

    _defaults = {
        'is_send':False,
        'deposit_margin':False,
        'is_type':'contract',
        'is_payment':False,
        'customer_id':get_customer_id,
        'receive_id':get_customer_id,
    }
    # 进入报关报检状态
    def btn_bill_customs(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'customs_dec'})

    # 进入报关报检状态
    def btn_redeem_customs(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'customs_dec'})

    # 进入赎车状态
    def btn_bill_redeem(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'car'})


    # 进入结算状态
    def btn_bill_payment(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'except_invoice'})

    # 进入收货通知状态
    def btn_confirmed_bill(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'customs'})

    # 进入收货通知状态
    def btn_redeem_bill(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'customs'})

    # 报关报检确认完成
    def btn_confirmed_done(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.purchase_type == 'agency_in':
            return self.write(cr, uid, ids, {'state':'car'})
        if obj.purchase_type == 'own_in':
            if obj.deposit_margin and not obj.new_pay:
                return self.write(cr, uid, ids, {'state':'except_invoice'})
            else:
                return self.write(cr, uid, ids, {'state':'done'})

    # 费用
    def btn_purchase_order(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'purchase', 'purchase_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'purchase', 'purchase_order_form')
        view_id_form = result_form and result_form[1] or False
        obj = self.browse(cr, uid, ids[0])
        location_model, location_ids = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        agency_ids = agency_obj.search(cr, uid, [('contract_id','=',ids[0]),('margin_log','=',False)])
        agency_ids_obj = agency_obj.browse(cr, uid, agency_ids[0])
        if obj.purchase_type == 'agency_in':
            partner_id = agency_ids_obj.agent_id
        if obj.purchase_type == 'own_in':
            partner_id = obj.partner_id
        order_obj = self.pool.get('purchase.order')
        res_id = order_obj.create(cr, uid, {'contract_id_three':ids[0],'partner_id':partner_id.id,'location_id':location_ids,'pricelist_id':partner_id.property_product_pricelist_purchase and partner_id.property_product_pricelist_purchase.id or False,
                                            'currency_id':partner_id.property_product_pricelist_purchase.currency_id.id})
        return {
              'name': _('询价单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'purchase.order',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',res_id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 查看费用
    def btn_payment_in(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'purchase', 'purchase_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'purchase', 'purchase_order_form')
        view_id_form = result_form and result_form[1] or False
        order_obj = self.pool.get('purchase.order')
        res_id = order_obj.search(cr, uid, [('contract_id_three','=',ids[0])])
        return {
              'name': _('采购单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'purchase.order',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',res_id)],
              'context':{'contract_id_three':ids[0]},
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 委托协议驳回
    def btn_cancel_contract_agent(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        if obj.new_id.state not in ('draft','confirmed'):
            raise osv.except_osv(u'警告', "进口合同已签订，无法驳回!")
        agency_ids = agency_obj.search(cr, uid, [('contract_id','=',obj.id),('state','!=','cancel')])
        if agency_ids:
            raise osv.except_osv(u'警告', "存在有效的委托协议，无法驳回!")
        return self.write(cr, uid, ids, {'state':'approved'})

    # 取消
    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'cancel'})

    # 签进口合同
    def btn_create_contract(self, cr, uid, ids, context=None):
        # 创建进口合同
        obj = self.browse(cr, uid, ids[0])
        new_obj = self.pool.get('qdodoo.car.in.contract.new')
        if not obj.new_id:
            res_id = new_obj.create(cr, uid, {'old_id':ids[0],'customer_id':obj.customer_id.id,'receive_id':obj.receive_id.id,'partner_id':obj.partner_id.id,'pricelist_id':obj.pricelist_id.id,
                                              'currency_id':obj.currency_id.id,'supplier_contract_version':obj.supplier_contract_version.id,'deposit_rate':obj.deposit_rate,'deposit_amount':obj.deposit_amount,
                                              'deposit_margin':obj.deposit_margin,'date_order':datetime.now(),'in_port':obj.in_port.id,'out_port':obj.out_port.id,'partial_shipment':obj.partial_shipment,
                                              'trans_shipment':obj.trans_shipment,'payment_line':obj.payment_line.id,'last_ship_date':obj.last_ship_date,'location_id':obj.location_id.id,'is_type':'contract_new','payment_type':obj.payment_type.id})
            for key in obj.order_line:
                key.copy({'order_id':res_id})
            # res_id = self.copy(cr, uid, ids[0],{'is_type':'contract_new'})
            self.write(cr, uid, ids, {'new_id':res_id})
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_car_in_contract_new')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_car_in_contract_new')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('进口合同'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.in.contract.new',
              'type': 'ir.actions.act_window',
              'domain':[('old_id','=',ids[0])],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    def onchange_deposit_amount(self, cr, uid, ids, deposit_rate):
        if isinstance(ids,(int,long)):
            ids = [ids]
        val = {}
        if ids:
            if deposit_rate:
                obj = self.browse(cr, uid, ids[0])
                if obj and obj.amount_total:
                    val['deposit_amount'] = obj.amount_total * deposit_rate / 100
        return {'value':val}

    # 收货通知单
    def btn_bill(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_car_bill_lading')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_car_bill_lading')
        view_id_form = result_form and result_form[1] or False
        lading_obj = self.pool.get('qdodoo.car.bill.lading')
        archives_obj = self.pool.get('qdodoo.car.archives')
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        lading_ids_new = lading_obj.search(cr, uid, [('contract_id','=',ids[0]),('state','=','draft')])
        lading_ids = lading_obj.search(cr, uid, [('contract_id','=',ids[0])])
        archives_ids = archives_obj.search(cr, uid, [('contract_id','=',ids[0])])
        agency_ids = agency_obj.search(cr, uid, [('contract_id','=',ids[0]),('margin_log','=',False)])
        agency_id = agency_ids[0] if agency_ids else False
        obj = self.browse(cr, uid, ids[0])
        # 获取委托协议服务费
        num = 0
        for line_key in agency_obj.browse(cr, uid, agency_id).order_line:
            num += line_key.agency_amount
        # 如果没有创建车辆档案
        if not archives_ids:
            # 创建车辆档案
            for line in obj.order_line:
                for one_line in range(int(line.product_qty)):
                    archives_obj.create(cr, uid, {'agent_margin_price':num,'import_pay_money':obj.deposit_amount/obj.amount_total*line.price_unit,'import_number':obj.new_id.id if obj.new_id else False,'agency_id':agency_id,'contract_id':ids[0],'car_model':line.product_id.id,'car_sale_price':line.price_unit})
        # 如果没有草稿状态的收货通知单，创建收货通知单
        if not lading_ids_new:
            archives_id = archives_obj.search(cr, uid, [('contract_id','=',ids[0]),('name','=',False)])
            if archives_id:
                res_id = lading_obj.create(cr, uid, {'in_port':obj.in_port.id,'out_port':obj.out_port.id,'contract_id':ids[0],
                                                     'contract_new_id':obj.new_id.id,'partner_id':obj.agency_id.partner_id.id,'in_partner_id':obj.agency_id.agent_id.id})
                lading_ids.append(res_id)

        return {
              'name': _('收货通知单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.bill.lading',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',lading_ids)],
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
            if not inv_data.get('date_invoice'):
                inv_data['date_invoice'] = datetime.now().date()
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

    # 查看赎车单
    def btn_select_redeem(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        lst_obj = []
        line_obj = self.pool.get('qdodoo.redeem.car.line')
        archives_obj = self.pool.get('qdodoo.car.archives')
        # 查询出所有该进口协议的车辆档案
        archives_ids = archives_obj.search(cr, uid, [('contract_id','=',obj.id)])
        # 查询赎车明细中存在这些车辆的明细
        line_obj_ids = line_obj.search(cr, uid, [('car_department','in',archives_ids)])
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

    # 创建赎车单
    def btn_redeem(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        lst_obj = []
        line_obj = self.pool.get('qdodoo.redeem.car.line')
        line_new_obj = self.pool.get('qdodoo.redeem.car')
        archives_obj = self.pool.get('qdodoo.car.archives')
        # 查询出所有该进口协议的车辆档案
        archives_ids = archives_obj.search(cr, uid, [('contract_id','=',obj.id)])
        # 查询赎车明细中存在这些车辆的明细
        line_obj_ids = line_obj.search(cr, uid, [('car_department','in',archives_ids)])
        for line_obj_id in line_obj.browse(cr, uid, line_obj_ids):
            if line_obj_id.redeem_apply_number.id not in lst_obj:
                lst_obj.append(line_obj_id.redeem_apply_number.id)
        # 创建赎车单
        res_id = line_new_obj.create(cr, uid, {'in_partner_id':obj.receive_id.id})
        lst_obj.append(res_id)
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

    # 确认结算单
    def btn_payment_order_done(self, cr, uid, ids, context=None):
        settlement_obj = self.pool.get('qdodoo.settlement.order')
        line_obj = self.pool.get('account.move.line')
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        obj = self.browse(cr, uid, ids[0])
        # 先删除所有数据
        settlement_ids = settlement_obj.search(cr, uid, [])
        settlement_obj.unlink(cr, uid, settlement_ids)
        # 获取本位币币种
        # currency_id = obj.company_id.currency_id.id
        # 获取辅助核算项
        analytic_lst = [obj.analytic_id.id]
        agency_ids = agency_obj.search(cr, uid, [('contract_id','=',ids[0]),('state','!=','cancel')])
        for line in agency_obj.browse(cr, uid, agency_ids):
            analytic_lst.append(line.analytic_id.id)
        if analytic_lst:
            num = 0
            line_ids = line_obj.search(cr, uid, [('analytic_account_id','in',analytic_lst)])
            for line in line_obj.browse(cr, uid, line_ids):
                if line.account_id.type == 'payable':
                    num += line.credit
                    num -= line.debit
            if abs(num) > 0.01:
                raise osv.except_osv(u'警告', "金额出现差异，结算无法完成!")
        return False
        return self.write(cr, uid, ids, {'state':'done'})

    # 结算单
    def btn_payment_order(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_settlement_order')
        view_id = result and result[1] or False
        settlement_obj = self.pool.get('qdodoo.settlement.order')
        line_obj = self.pool.get('account.move.line')
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        obj = self.browse(cr, uid, ids[0])
        # 先删除所有数据
        settlement_ids = settlement_obj.search(cr, uid, [])
        settlement_obj.unlink(cr, uid, settlement_ids)
        # 获取本位币币种
        # currency_id = obj.company_id.currency_id.id
        # 获取辅助核算项
        analytic_lst = [obj.analytic_id.id]
        agency_ids = agency_obj.search(cr, uid, [('contract_id','=',ids[0]),('state','!=','cancel')])
        for line in agency_obj.browse(cr, uid, agency_ids):
            analytic_lst.append(line.analytic_id.id)
        if analytic_lst:
            line_ids = line_obj.search(cr, uid, [('analytic_account_id','in',analytic_lst)])
            for line in line_obj.browse(cr, uid, line_ids):
                if line.account_id.type == 'payable':
                    val = {'ref':line.name,'partner_id':line.partner_id.id,'date':line.date,'contract_id':ids[0],'account_id':line.analytic_account_id.id,
                                                    'own_amount':line.credit,'in_amount':line.debit}
                    if line.amount_currency < 0:
                        val['out_amount'] = -line.amount_currency
                        val['exchange_rate'] = line.currency_id.rate_silent
                        val['currency_id'] = line.currency_id.id
                    settlement_obj.create(cr, uid, val)
            search = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_search_qdodoo_settlement_order')
            search_id = search and search[1] or False
            return {
                  'name': _('结算单'),
                  'view_type': 'form',
                  "view_mode": 'tree',
                  'res_model': 'qdodoo.settlement.order',
                  'type': 'ir.actions.act_window',
                  'views': [(view_id,'tree')],
                  'search_view_id': [search_id],
                  'context': {'search_default_group_by_partner_id':True},
                  'view_id': [view_id],
                  }

    # 委托代理按钮
    def btn_entrust_agent(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        if obj.purchase_type == 'agency_in':
            agency_ids_new = agency_obj.search(cr, uid, [('contract_id','=',ids[0]),('state','!=','cancel'),('margin_log','=',False)])
        else:
            agency_ids_new = agency_obj.search(cr, uid, [('contract_id','=',ids[0]),('state','!=','cancel')])
        agency_ids = agency_obj.search(cr, uid, [('contract_id','=',ids[0])])
        if not agency_ids_new:
            val = {}
            if obj.contract_number:
                val['import_contract_number'] = obj.contract_number
            val['purchase_type'] = obj.purchase_type
            val['deposit_rate'] = obj.deposit_amount
            val['shipment_date'] = obj.last_ship_date
            val['deposit_margin'] = obj.deposit_margin
            val['contract_id'] = obj.id
            val['partner_id'] = obj.partner_id.id
            val['in_port'] = obj.in_port.id
            val['out_port'] = obj.out_port.id
            val['partial_shipment'] = obj.partial_shipment
            val['trans_shipment'] = obj.trans_shipment
            val['payment_type'] = obj.payment_type.id
            val['payment_line'] = obj.payment_line.id
            val['currency_id'] = obj.currency_id.id
            val['new_pay'] = obj.new_pay
            val['insurance_type'] = u'全险'
            if obj.new_pay and obj.purchase_type=='own_in':
                val['margin_log'] = True
                val['margin_own'] = True
            res_id = agency_obj.create(cr, uid, val, context=context)
            obj.order_line.copy({'order_id':False,'entrusted_id':res_id})
            agency_ids = []
            agency_ids.append(res_id)
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
              'domain':[('id','in',agency_ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 查看委托协议
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

    # 查看收货通知
    def btn_receive_notice(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_car_bill_lading')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_car_bill_lading')
        view_id_form = result_form and result_form[1] or False
        lading_obj = self.pool.get('qdodoo.car.bill.lading')
        lst = lading_obj.search(cr, uid, [('contract_id','=',ids[0])])
        return {
              'name': _('收货通知'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.bill.lading',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',lst)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 查看进口合同
    def btn_read_bill_lading(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_car_in_contract_new')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_car_in_contract_new')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('进口合同'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.in.contract.new',
              'type': 'ir.actions.act_window',
              'domain':[('old_id','in',ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 查看账务（财务分录）
    def btn_read_payment_order(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_line_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_line_form')
        view_id_form = result_form and result_form[1] or False
        obj = self.browse(cr, uid, ids[0])
        ids_lst = [obj.analytic_id.id]
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        agency_ids = agency_obj.search(cr, uid, [('contract_id','=',obj.id)])
        for line in agency_obj.browse(cr, uid, agency_ids):
            if line.analytic_id:
                ids_lst.append(line.analytic_id.id)
        return {
              'name': _('账务分录'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'account.move.line',
              'type': 'ir.actions.act_window',
              'domain':[('analytic_account_id','in',ids_lst),('analytic_account_id','!=',False)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 付款通知
    def btn_payment_message(self, cr, uid, ids, context=None):
        payment_obj = self.pool.get('qdodoo.payment.order')
        payment_id = payment_obj.search(cr, uid, [('contract_id','=',ids[0])])
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
        view_id_form = result_form and result_form[1] or False
        if not payment_id:
            context['default_model'] = 'contract_id'
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

    # 生成入库单的函数
    def action_picking_create(self, cr, uid, ids, lading_id=False, lading_new_id=False, context=None):
        for order in self.browse(cr, uid, ids):
            picking_vals = {
                'picking_type_id': order.picking_type_id.id,
                'partner_id': order.partner_id.id,
                'date': order.date_order,
                'origin': order.name,
                'contract_id':order.id,
                'lading_id':lading_id,
                'lading_new_id':lading_new_id
            }
            picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
            self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)
        return picking_id

    # 确认订单
    def act_approved(self):
        if not self.contract_type:
            raise osv.except_osv(u'警告', "请先输入采购渠道!")
        if not self.in_port:
            raise osv.except_osv(u'警告', "请先输入发货港!")
        if not self.payment_type:
            raise osv.except_osv(u'警告', "请先输入付款方式!")
        for line in self.order_line:
            if line.price_unit <= 0:
                raise osv.except_osv(u'警告', "货物明细中不能存在单价为0的数据!")
        location_model_cus, location_cus_ids = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'ir_cron_account_analytic_account')
        analytic_obj = self.env['account.analytic.account']
        val = {}
        val['name'] = self.name
        val['type'] = 'normal'
        val['parent_id'] = location_cus_ids
        res_id = analytic_obj.create(val)
        invoice_id = self.action_invoice_create(res_id.id)
        if self.contract_type == 'out':
            return self.write({'state':'approved','analytic_id':res_id.id,'invoice_id':invoice_id})
        if self.contract_type == 'in':
            return self.write({'state':'lc','analytic_id':res_id.id,'purchase_type':'own','invoice_id':invoice_id})

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
        if not vals.get('old_id'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.in.contract')
        return super(qdodoo_car_in_contract, self).create(vals)

    def write(self, cr, uid, ids, value, context=None):
        if isinstance(ids,(int,long)):
            ids = [ids]
        if not context:
            context = {}
        if not context.get('new_id'):
            obj = self.browse(cr, uid, ids[0])
            if value.get('contract_number'):
                value['name'] = value.get('contract_number') + '-' + obj.name
            if value.get('state') == 'sent':
                line_obj = self.pool.get('purchase.order.line')
                for line in obj.order_line:
                    line_obj.write(cr, uid, line.id, {'state':'confirmed'})
            # 将所有收货通知单置为完成
            if value.get('state') == 'done':
                contract_new_obj = self.pool.get('qdodoo.car.in.contract.new')
                contract_new_obj.write(cr, uid, obj.new_id.id, {'state':'done'})
        return super(qdodoo_car_in_contract, self).write(cr, uid, ids, value, context=context)

class qdodoo_car_in_contract_new(models.Model):
    """
        进口合同
    """
    _name = 'qdodoo.car.in.contract.new'    # 模型名称
    _inherit = 'qdodoo.car.in.contract'
    _table = "purchase_order"
    _rec_name = 'contract_number'

    STATE_SELECTION = [
        ('draft', u'草稿'),
        ('confirmed', u'合同签订'),
        ('approved', u'支付定金'),
        ('except_picking', u'合同执行'),
        ('done', u'完成'),
        ('cancel', u'已取消')
    ]

    state = fields.Selection(STATE_SELECTION, u'状态', readonly=True,
                                  select=True, copy=False)
    old_id = fields.Many2one('qdodoo.car.in.contract',u'整车采购',copy=False)
    purchase_type = fields.Selection([('agency_in',u'委托进口'),('own_in',u'自营进口')],u'采购渠道')

    _defaults = {
        'is_type':'contract_new',
        'state':'draft',
        'new_pay':False
    }

    # 查看收货通知单
    def btn_read_bill_lading(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_car_bill_lading')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_car_bill_lading')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('收货通知单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.bill.lading',
              'type': 'ir.actions.act_window',
              'domain':[('contract_new_id','in',ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 查看委托协议
    def btn_read_entrusted_agency(self, cr, uid, ids, context=None):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_tree_qdodoo_entrusted_agency')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_form_qdodoo_entrusted_agency')
        view_id_form = result_form and result_form[1] or False
        obj = self.browse(cr, uid, ids[0])
        return {
              'name': _('委托代理'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.entrusted.agency',
              'type': 'ir.actions.act_window',
              'domain':[('contract_id','=',obj.old_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }

    # 付款通知
    def btn_payment_message(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if not obj.deposit_amount:
            return self.write(cr, uid, ids, {'state':'except_picking'})
        payment_obj = self.pool.get('qdodoo.payment.order')
        payment_id = payment_obj.search(cr, uid, [('contract_new_id','=',ids[0])])
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
        view_id_form = result_form and result_form[1] or False
        if not payment_id:
            context['default_model'] = 'contract_new_id'
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

    # 已签订合同
    def btn_old_contract(self, cr, uid, ids, context=None):
        location_model_cus, location_cus_ids = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'ir_cron_account_analytic_account_new')
        analytic_obj = self.pool.get('account.analytic.account')
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        obj = self.browse(cr, uid, ids[0])
        agency_ids = agency_obj.search(cr, uid, [('contract_id','=',obj.old_id.id),('state','!=','cancel')])
        if not obj.contract_number:
            raise osv.except_osv(u'警告', "请先输入进口合同号!")
        if not obj.contract_date:
            raise osv.except_osv(u'警告', "请先输入合同日期!")
        if not obj.contract_note:
            raise osv.except_osv(u'警告', "请先上传合同原件!")
        if (not agency_ids and obj.purchase_type == 'agency_in') or (not agency_ids and obj.new_pay and obj.purchase_type == 'own_in'):
            raise osv.except_osv(u'警告', "请先创建对应的委托协议!")
        if obj.purchase_type == 'own_in' and not obj.new_pay:
            contract_obj.write(cr, uid, obj.old_id.id, {'state':'lc'})
        analytic_obj.write(cr, uid, obj.old_id.analytic_id.id, {'name':obj.contract_number +'-'+ obj.old_id.analytic_id.name})
        self.write(cr, uid, ids[0], {'analytic_id':obj.old_id.analytic_id.id})
        if agency_ids:
            agency_obj.write(cr, uid, agency_ids, {'import_contract_number':obj.contract_number})
        contract_obj.write(cr, uid, obj.old_id.id, {'new_pay':obj.new_pay,'contract_number':obj.contract_number,'contract_date':obj.contract_date})
        if obj.new_pay:
            self.write(cr, uid, ids[0], {'state':'except_picking'})
        else:
            self.write(cr, uid, ids[0], {'state':'approved'})
        return True

    # 驳回
    def btn_cancel_contract(self, cr, uid, ids, context=None):
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        obj = self.browse(cr, uid, ids[0])
        if obj.old_id.agency_id:
            raise osv.except_osv(u'警告', "存在有效的委托协议，无法驳回!")
        self.write(cr, uid, ids, {'state':'draft'})
        contract_obj.write(cr, uid, obj.old_id.id, {'state':'approved'})
        return True

    # 确认合同
    def btn_create_contract(self, cr, uid, ids, context=None):
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        obj = self.browse(cr, uid, ids[0])
        contract_obj.write(cr, uid, obj.old_id.id, {'purchase_type':obj.purchase_type})
        if obj.purchase_type == 'agency_in' or (obj.purchase_type == 'own_in' and obj.new_pay and obj.deposit_amount):
            contract_obj.write(cr, uid, obj.old_id.id, {'state':'except_picking','new_pay':obj.new_pay})
        return self.write(cr, uid, ids, {'state':'confirmed'})

    def btn_confirmed_sent(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'draft'})

    def btn_message(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'draft'})

    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        # self.write(cr, uid, ids, {'state':'confirmed'})
        return self.pool['report'].get_action(cr, uid, ids, 'qdodoo_car_import_trade.report_qdodoo_car_import', context=context)

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

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('qdodoo.car.in.contract.new')
        return super(qdodoo_car_in_contract_new, self).create(vals)

    def write(self, cr, uid, ids, value, context=None):
        if isinstance(ids,(int,long)):
            ids = [ids]
        account_obj = self.pool.get('account.invoice')
        if ids:
            if value.get('contract_number'):
                search_id = self.search(cr, uid, [('contract_number','=',value.get('contract_number'))])
                if search_id:
                    raise osv.except_osv(u'警告', "已存在的进口合同号!")
            super(qdodoo_car_in_contract_new, self).write(cr, uid, ids, value, context={'new_id':True})
            obj = self.browse(cr, uid, ids[0])
            if value.get('state') == 'cancel':
                contract_obj = self.pool.get('qdodoo.car.in.contract')
                contract_obj.write(cr, uid, [obj.old_id.id], {'new_id':False})
            if value.get('state') == 'except_picking':
                if obj.old_id.invoice_id.state == 'draft':
                    account_obj.signal_workflow(cr, uid, [obj.old_id.invoice_id.id], 'invoice_open')
        return True

class qdodoo_stock_transfer_details_items_inherit(models.Model):
    _inherit = 'stock.transfer_details_items'

    car_name = fields.Many2one('qdodoo.car.archives',u'车架号')
    # lading_id = fields.Many2one('qdodoo.car.bill.lading',u'收货通知单',related='transfer_id.picking_id.lading_id')

class qdodoo_stock_picking_inherit(models.Model):
    _inherit = 'stock.picking'

    contract_id = fields.Many2one('qdodoo.car.in.contract',u'合同')
    lading_id = fields.Many2one('qdodoo.car.bill.lading',u'收货通知单')
    lading_new_id = fields.Many2one('qdodoo.car.bill.lading',u'收货通知单')
    car_number = fields.Char(u'车架号集合',copy=False)
    car_number_return = fields.Char(u'反向转移车架号集合',copy=False)

    # 入库转移时，更新对应整车采购订单的状态
    @api.one
    def do_transfer(self):
        res = super(qdodoo_stock_picking_inherit, self).do_transfer()
        transfer_details_items_obj = self.env['stock.transfer_details'].search([('picking_id','=',self.id)])[-1]
        if self.lading_id:
            key = ''
            for car_id in transfer_details_items_obj.item_ids:
                car_id.car_name.write({'is_log':True,'location_id':car_id.destinationloc_id.id})
                key += (str(car_id.car_name.id) + ',')
            self.write({'car_number':self.car_number+','+key if self.car_number else key})
            self.lading_id.write({'state':'tra'})
        elif self.lading_new_id:
            key = ''
            for car_id in transfer_details_items_obj.item_ids:
                car_id.car_name.write({'is_log_two':True,'location_id':car_id.destinationloc_id.id})
                key += (str(car_id.car_name.id) + ',')
            self.write({'car_number':self.car_number+','+key if self.car_number else key})
            res_id = self.search([('state','not in',('done','cancel')),('lading_new_id','=',self.lading_new_id.id)])
            if not res_id:
                self.lading_new_id.write({'state':'done'})
        elif self.picking_type_id.code == 'outgoing' and not self.lading_new_id and not self.lading_id:
            # 获取此次源单据id
            origin_id = self.env['sale.order'].search([('name','=',self.origin)])
            origin = origin_id and origin_id[0].id or False
            key = ''
            for car_id in transfer_details_items_obj.item_ids:
                if car_id.car_name:
                    key += (str(car_id.car_name.id) + ',')
                    car_id.car_name.write({'is_sale':True,'sale_order':origin,'location_id':car_id.destinationloc_id.id})
            self.write({'car_number':self.car_number+','+key if self.car_number else key})
        else:
            key = ''
            for car_id in transfer_details_items_obj.item_ids:
                if car_id.car_name:
                    key += (str(car_id.car_name.id) + ',')
                    car_id.car_name.write({'location_id':car_id.destinationloc_id.id})
            self.write({'car_number':self.car_number+','+key if self.car_number else key})
        return res

    # 转移时，如果部分转移，生成的新的单据也要关联收货通知单
    def _create_backorder(self, cr, uid, picking, backorder_moves=[], context=None):
        """ Move all non-done lines into a new backorder picking. If the key 'do_only_split' is given in the context, then move all lines not in context.get('split', []) instead of all non-done lines.
        """
        if not backorder_moves:
            backorder_moves = picking.move_lines
        backorder_move_ids = [x.id for x in backorder_moves if x.state not in ('done', 'cancel')]
        if 'do_only_split' in context and context['do_only_split']:
            backorder_move_ids = [x.id for x in backorder_moves if x.id not in context.get('split', [])]

        if backorder_move_ids:
            backorder_id = self.copy(cr, uid, picking.id, {
                'name': '/',
                'move_lines': [],
                'pack_operation_ids': [],
                'backorder_id': picking.id,
                'lading_new_id':picking.lading_new_id and picking.lading_new_id.id or False
            })
            backorder = self.browse(cr, uid, backorder_id, context=context)
            self.message_post(cr, uid, picking.id, body=_("Back order <em>%s</em> <b>created</b>.") % (backorder.name), context=context)
            move_obj = self.pool.get("stock.move")
            move_obj.write(cr, uid, backorder_move_ids, {'picking_id': backorder_id}, context=context)

            if not picking.date_done:
                self.write(cr, uid, [picking.id], {'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
            self.action_confirm(cr, uid, [backorder_id], context=context)
            return backorder_id
        return False

    @api.cr_uid_ids_context
    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        if not context:
            context = {}
        context.update({
            'active_model': self._name,
            'active_ids': picking,
            'active_id': len(picking) and picking[0] or False
        })
        created_id = self.pool['stock.transfer_details'].create(cr, uid, {'picking_id': len(picking) and picking[0] or False}, context)
        # 获取收货通知单模型
        picking_obj = self.pool['stock.picking'].browse(cr, uid, picking[0])
        lading_obj_1 = picking_obj.lading_id
        lading_obj_2 = picking_obj.lading_new_id
        lading_obj = lading_obj_1 and lading_obj_1 or lading_obj_2
        if picking and lading_obj or picking_obj.car_number_return:
            transfer_details_obj = self.pool['stock.transfer_details']
            transfer_details_items_obj = self.pool['stock.transfer_details_items']
            obj = transfer_details_obj.browse(cr, uid, created_id)
            # 获取收货通知单中的产品和数量字段{产品：数量}{产品：[车架号]}
            dict_lading = {}
            dict_name = {}
            dict_car = {}
            dict_log = {}
            dict_log_two = {}
            # 反向转移产生的调拨单
            if picking_obj.car_number_return:
                # 获取对应的产品id和车架号id
                for line in picking_obj.car_number_return.split(';'):
                    if line:
                        key_id = int(line.split(':')[0])
                        value_id = int(line.split(':')[1])
                        if key_id in dict_lading:
                            dict_lading[key_id] += 1
                            dict_name[key_id].append(value_id)
                            dict_car[key_id].append(value_id)
                        else:
                            dict_lading[key_id] = 1
                            dict_name[key_id] = [value_id]
                            dict_car[key_id] = [value_id]
            for lst in lading_obj.order_line:
                if lading_obj_1:
                    if lst.name and not lst.is_log:
                        if lst.car_model.id in dict_lading :
                            dict_lading[lst.car_model.id] += 1
                            dict_name[lst.car_model.id].append(lst.id)
                            dict_car[lst.car_model.id].append(lst.id)
                        else:
                            dict_lading[lst.car_model.id] = 1
                            dict_name[lst.car_model.id] = [lst.id]
                            dict_car[lst.car_model.id] = [lst.id]
                            dict_log[lst.car_model.id] = True
                if lading_obj_2:
                    if lst.name and not lst.is_log_two:
                        if lst.car_model.id in dict_lading :
                            dict_lading[lst.car_model.id] += 1
                            dict_name[lst.car_model.id].append(lst.id)
                            dict_car[lst.car_model.id].append(lst.id)
                        else:
                            dict_lading[lst.car_model.id] = 1
                            dict_name[lst.car_model.id] = [lst.id]
                            dict_car[lst.car_model.id] = [lst.id]
                            dict_log_two[lst.car_model.id] = True
            # 按照数量拆分和添加车架号
            for line in obj.item_ids:
                if line.product_id.id in dict_lading:
                    obj_id = line.id
                    if line.quantity > 1 and dict_lading[line.product_id.id] >1 :
                        transfer_details_items_obj.write(cr, uid, obj_id, {'quantity':1,'car_name':dict_name[line.product_id.id][0]})
                        # self.pool['qdodoo.car.archives'].write(cr, uid, dict_car[line.product_id.id][0], {'is_log':dict_log.get(line.product_id.id,False),'is_log_two':dict_log_two.get(line.product_id.id,False)})
                        del dict_name[line.product_id.id][0]
                        for i in range(1,int(dict_lading[line.product_id.id])):
                            transfer_details_items_obj.copy(cr, uid, obj_id, {'packop_id':False,'quantity':1,'car_name':dict_name[line.product_id.id][0]})
                            # self.pool['qdodoo.car.archives'].write(cr, uid, dict_car[line.product_id.id][0], {'is_log':dict_log.get(line.product_id.id,False),'is_log_two':dict_log_two.get(line.product_id.id,False)})
                            del dict_name[line.product_id.id][0]
                    else:
                        transfer_details_items_obj.write(cr, uid, obj_id, {'quantity':1,'car_name':dict_name[line.product_id.id][0]})
                        # self.pool['qdodoo.car.archives'].write(cr, uid, dict_car[line.product_id.id][0], {'is_log':dict_log.get(line.product_id.id,False),'is_log_two':dict_log_two.get(line.product_id.id,False)})
                        del dict_name[line.product_id.id][0]
                else:
                    transfer_details_items_obj.unlink(cr, uid, line.id)
        return self.pool['stock.transfer_details'].wizard_view(cr, uid, created_id, context)

    # 获取{产品id：进口价}
    def get_import_price(self, cr, uid, ids, contract_id, context=None):
        valu = {}
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        for contract_obj_ids in contract_obj.browse(cr, uid, contract_id):
            for contract_obj_id in contract_obj_ids.order_line:
                valu[contract_obj_id.product_id.id] = contract_obj_id.price_subtotal
        return valu

class qdodoo_stock_return_picking_inherit(models.Model):
    _inherit = 'stock.return.picking'

    # 获取车架号
    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        result1 = []
        if context is None:
            context = {}
        if context and context.get('active_ids', False):
            if len(context.get('active_ids')) > 1:
                raise osv.except_osv(_('Warning!'), _("You may only return one picking at a time!"))
        res = super(qdodoo_stock_return_picking_inherit, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        uom_obj = self.pool.get('product.uom')
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        quant_obj = self.pool.get("stock.quant")
        chained_move_exist = False
        if pick:
            if pick.state != 'done':
                raise osv.except_osv(_('Warning!'), _("You may only return pickings that are Done!"))
            for move in pick.move_lines:
                if move.move_dest_id:
                    chained_move_exist = True
                #Sum the quants in that location that can be returned (they should have been moved by the moves that were included in the returned picking)
                qty = 0
                quant_search = quant_obj.search(cr, uid, [('history_ids', 'in', move.id), ('qty', '>', 0.0), ('location_id', 'child_of', move.location_dest_id.id)], context=context)
                for quant in quant_obj.browse(cr, uid, quant_search, context=context):
                    if not quant.reservation_id or quant.reservation_id.origin_returned_move_id.id != move.id:
                        qty += quant.qty
                qty = uom_obj._compute_qty(cr, uid, move.product_id.uom_id.id, qty, move.product_uom.id)
                car_number = ''
                if qty > 1:
                    for i in range(int(qty)):
                        if pick.car_number:
                            car_number = int(pick.car_number.split(',')[i])
                        result1.append({'car_number':car_number,'product_id': move.product_id.id, 'quantity': 1, 'move_id': move.id})
                else:
                    if pick.car_number:
                        car_number = int(pick.car_number.split(',')[0])
                    result1.append({'car_number':car_number,'product_id': move.product_id.id, 'quantity': qty, 'move_id': move.id})

            if len(result1) == 0:
                raise osv.except_osv(_('Warning!'), _("No products to return (only lines in Done state and not fully returned yet can be returned)!"))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': result1})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': chained_move_exist})
        return res

    def create_returns(self, cr, uid, ids, context=None):
        res_id = super(qdodoo_stock_return_picking_inherit, self).create_returns(cr, uid, ids, context=context)
        obj = self.browse(cr, uid, ids[0])
        lst = []
        return_number = ''
        for line in obj.product_return_moves:
            if line.car_number:
                return_number += (str(line.product_id.id) + ':' + str(line.car_number.id) + ';')
                lst.append(line.car_number.id)
        key_id = int(res_id.get('domain').split(']',1)[0].split('[',-1)[-1])
        self.pool.get('qdodoo.car.archives').write(cr, 1, lst, {'is_sale':False,'sale_order':''})
        self.pool.get('stock.picking').write(cr, uid, key_id,{'car_number_return':return_number})
        return res_id

class qdodoo_stock_return_picking_line_inherit(models.Model):
    _inherit = 'stock.return.picking.line'

    car_number = fields.Many2one('qdodoo.car.archives',u'车架号')

class qdodoo_mail_compose_message_inherit(models.Model):
    _inherit = ['mail.compose.message']
    def send_mail(self, cr, uid, ids, context=None):
        if context.get('is_contract'):
            obj = self.pool.get('qdodoo.car.in.contract')
            obj.signal_workflow(cr, uid, context.get('active_ids'), 'send_rfq')
        return super(qdodoo_mail_compose_message_inherit, self).send_mail(cr, uid, ids, context=context)

class qdodoo_res_partner_bank(models.Model):
    _inherit = 'res.partner.bank'

    is_defaults = fields.Boolean(u'默认账户')

    _defaults = {
        'is_defaults':False,
    }

# class qdodoo_product_product_inherit(models.Model):
#     _inherit = 'product.product'
#
#     brand_id = fields.Many2one('qdodoo.product.brand',u'品牌')
#     version_id = fields.Many2one('qdodoo.version',u'版本')
#     series_id = fields.Many2one('qdodoo.series.of',u'系列')
#     year_id = fields.Many2one('qdodoo.product.year',u'年款')
#     model_id = fields.Many2one('qdodoo.model',u'型号')
#     appearance_id = fields.Many2one('qdodoo.appearance',u'外观')
#     interior_id = fields.Many2one('qdodoo.interior',u'内饰')
#     configuration_id = fields.Many2one('qdodoo.configuration',u'配置')
#
#     def name_get(self, cr, uid, ids, context=None):
#         """Overides orm name_get method to display 'Warehouse_name: PickingType_name' """
#         if context is None:
#             context = {}
#         if not isinstance(ids, list):
#             ids = [ids]
#         res_ids = super(qdodoo_product_product_inherit, self).name_get(cr, uid, ids, context=context)
#         res = []
#         if not ids:
#             return res
#         for res_id in res_ids:
#             for record in self.browse(cr, uid, res_id[0], context=context):
#                 name = ''
#                 if record.year_id:
#                     name += record.year_id.name
#                 if record.brand_id:
#                     name += record.brand_id.name
#                 if record.series_id:
#                     name += record.series_id.name
#                 if record.model_id:
#                     name += record.model_id.name
#                 if record.version_id:
#                     name += record.version_id.name
#                 if record.appearance_id:
#                     name += record.appearance_id.name
#                 if record.interior_id:
#                     name += record.interior_id.name
#                 if record.configuration_id:
#                     name += record.configuration_id.name
#                 name += record.name
#                 res.append((record.id, name))
#         return res

# class qdodoo_product_template_inherit(models.Model):
#     _inherit = 'product.template'
#
#     year_id = fields.Many2one('qdodoo.product.year',u'年款')
#     brand_id = fields.Many2one('qdodoo.product.brand',u'品牌')
#     series_id = fields.Many2one('qdodoo.series.of',u'系列')
#     model_id = fields.Many2one('qdodoo.model',u'型号')
#     version_id = fields.Many2one('qdodoo.version',u'版本')
#     appearance_id = fields.Many2one('qdodoo.appearance',u'外观')
#     interior_id = fields.Many2one('qdodoo.interior',u'内饰')
#     configuration_id = fields.Many2one('qdodoo.configuration',u'配置')
#
#     def create(self, cr, uid, vals, context=None):
#         val_dict = {}
#         if vals.get('year_id'):
#             val_dict['year_id'] = vals.get('year_id')
#         if vals.get('brand_id'):
#             val_dict['brand_id'] = vals.get('brand_id')
#         if vals.get('series_id'):
#             val_dict['series_id'] = vals.get('series_id')
#         if vals.get('model_id'):
#             val_dict['model_id'] = vals.get('model_id')
#         if vals.get('version_id'):
#             val_dict['version_id'] = vals.get('version_id')
#         if vals.get('appearance_id'):
#             val_dict['appearance_id'] = vals.get('appearance_id')
#         if vals.get('interior_id'):
#             val_dict['interior_id'] = vals.get('interior_id')
#         if vals.get('configuration_id'):
#             val_dict['configuration_id'] = vals.get('configuration_id')
#         res_id = super(qdodoo_product_template_inherit, self).create(cr, uid, vals, context=context)
#         if val_dict:
#             product_obj = self.pool.get('product.product')
#             product_ids = product_obj.search(cr, uid, [('product_tmpl_id','=',res_id)])
#             product_obj.write(cr, uid, product_ids, val_dict)
#         return res_id

    # def write(self, cr, uid, ids, vals, context=None):
    #     val_dict = {}
    #     if vals.get('year_id'):
    #         val_dict['year_id'] = vals.get('year_id')
    #     if vals.get('brand_id'):
    #         val_dict['brand_id'] = vals.get('brand_id')
    #     if vals.get('series_id'):
    #         val_dict['series_id'] = vals.get('series_id')
    #     if vals.get('model_id'):
    #         val_dict['model_id'] = vals.get('model_id')
    #     if vals.get('version_id'):
    #         val_dict['version_id'] = vals.get('version_id')
    #     if vals.get('appearance_id'):
    #         val_dict['appearance_id'] = vals.get('appearance_id')
    #     if vals.get('interior_id'):
    #         val_dict['interior_id'] = vals.get('interior_id')
    #     if vals.get('configuration_id'):
    #         val_dict['configuration_id'] = vals.get('configuration_id')
    #     if val_dict:
    #         product_obj = self.pool.get('product.product')
    #         product_ids = product_obj.search(cr, uid, [('product_tmpl_id','in',ids)])
    #         product_obj.write(cr, uid, product_ids, val_dict)
    #     return super(qdodoo_product_template_inherit, self).write(cr, uid, ids, vals, context=context)

class qdodoo_payment_model(models.Model):
    """
        选择付款方式
    """
    _name = 'qdodoo.payment.model'    # 模型名称

    name = fields.Many2one('payment.mode',u'付款方式',required=True)

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

    # 创建对应的付款通知单
    def search_date(self, cr, uid, ids,context=None):
        contract_obj = self.pool.get('qdodoo.car.in.contract')
        contract_new_obj = self.pool.get('qdodoo.car.in.contract.new')
        agency_obj = self.pool.get('qdodoo.entrusted.agency')
        redeem_obj = self.pool.get('qdodoo.redeem.car')
        # settlement_obj = self.pool.get('qdodoo.settlement.order')
        payment_obj = self.pool.get('qdodoo.payment.order')
        payment_line_obj = self.pool.get('payment.line')
        account_obj = self.pool.get('account.invoice')
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_car_import_trade', 'view_qdodoo_payment_order_form')
        view_id_form = result_form and result_form[1] or False
        vals = {}
        # 创建整车采购订单中付款通知单
        if context.get('default_model') == 'contract_id':
            id_lst = []
            obj = contract_obj.browse(cr, uid, ids[0])
            vals['payment_supplier'] = obj.partner_id.id
            vals['user_id'] = uid
            vals['partner_qdodoo_id'] = obj.partner_id.id
            vals['date_prefered'] = 'now'
            vals[context.get('default_model')] = obj.id
            res_id = payment_obj.create(cr, uid, vals, context=context)
            res_id_new = payment_obj.copy(cr, uid, res_id)
            id_lst.append(res_id)
            if obj.invoice_id:
                # account_obj.signal_workflow(cr, uid, [account_id[0]], 'invoice_open')
                val = {}
                val['order_id'] = res_id
                val['date'] = datetime.now().date()
                val['partner_id'] = obj.partner_id.id
                val['currency'] = obj.currency_id.id
                val['communication'] = obj.name
                val['invoice_id'] = obj.invoice_id.id
                val['communication2'] = "购车款"
                val['bank_id'] = self.get_partner_bank(cr, uid, ids, obj.partner_id.id)
                val['name'] = obj.pool.get('ir.sequence').get(cr, uid, 'payment.line')
                val['state'] = 'normal'
                # 如果有定金，产生两条付款通知单(内贸自营采购)
                if obj.purchase_type == 'own':
                    if obj.deposit_amount:
                        val['amount_currency'] = obj.deposit_amount
                        re_line_id = payment_line_obj.create(cr, uid, val, context=None)
                        payment_line_obj.copy(cr, uid, re_line_id,{'name':obj.pool.get('ir.sequence').get(cr, uid, 'payment.line'),'order_id':res_id_new,'amount_currency':obj.amount_total-obj.deposit_amount})
                        id_lst.append(res_id_new)
                        return id_lst
                    else:
                        payment_obj.unlink(cr, uid, res_id_new)
                        val['amount_currency'] = obj.amount_total
                        payment_line_obj.create(cr, uid, val, context=None)
                        return id_lst
                if obj.purchase_type == 'own_in':
                    payment_obj.unlink(cr, uid, res_id_new)
                    if obj.deposit_margin:
                        val['amount_currency'] = obj.amount_total
                    else:
                        val['amount_currency'] = obj.amount_total-obj.deposit_amount
                    payment_line_obj.create(cr, uid, val, context=None)
                return [res_id]
            else:
                if obj.purchase_type == 'own_in':
                    val = {}
                    val['order_id'] = res_id
                    val['date'] = datetime.now().date()
                    val['partner_id'] = obj.partner_id.id
                    val['currency'] = obj.currency_id.id
                    val['communication'] = obj.name
                    val['communication2'] = "自营进口支付货款"
                    val['bank_id'] = self.get_partner_bank(cr, uid, ids, obj.partner_id.id)
                    val['name'] = obj.pool.get('ir.sequence').get(cr, uid, 'payment.line')
                    val['state'] = 'normal'
                    val['amount_currency'] = obj.amount_total - obj.deposit_amount
                    re_line_id = payment_line_obj.create(cr, uid, val, context=None)
                    payment_obj.unlink(cr, uid, res_id_new)
                    return [res_id]
        # 创建进口合同中付款通知单
        if context.get('default_model') == 'contract_new_id':
            obj = contract_new_obj.browse(cr, uid, ids[0])
            vals['payment_supplier'] = obj.partner_id.id
            vals['user_id'] = uid
            vals['partner_qdodoo_id'] = obj.partner_id.id
            vals['date_prefered'] = 'now'
            vals[context.get('default_model')] = obj.id
            res_id = payment_obj.create(cr, uid, vals, context=context)
            if obj.old_id.invoice_id:
                # account_obj.signal_workflow(cr, uid, [account_id[0]], 'invoice_open')
                val = {}
                val['order_id'] = res_id
                val['date'] = datetime.now().date()
                # val['move_line_id'] = move_line_id
                val['partner_id'] = obj.partner_id.id
                val['currency'] = obj.currency_id.id
                val['communication'] = obj.name
                val['communication2'] = "履约保证金"
                if not obj.deposit_margin:
                    val['communication2'] = "定金"
                    val['invoice_id'] = obj.old_id.invoice_id.id
                val['bank_id'] = self.get_partner_bank(cr, uid, ids, obj.partner_id.id)
                val['name'] = obj.pool.get('ir.sequence').get(cr, uid, 'payment.line')
                val['state'] = 'normal'
                val['amount_currency'] = obj.deposit_amount
                payment_line_obj.create(cr, uid, val, context=None)
                return [res_id]
        # 创建委托协议中的付款通知单
        if context.get('default_model') == 'agency_id':
            res_lst = []
            obj = agency_obj.browse(cr, uid, ids[0])
            account_id = account_obj.search(cr, uid, [('origin','=',obj.name)])
            if account_id:
                vals['payment_supplier'] = obj.agent_id.id
                vals['user_id'] = uid
                vals['partner_qdodoo_id'] = obj.agent_id.id
                vals['date_prefered'] = 'now'
                vals[context.get('default_model')] = obj.id
                res_id = payment_obj.create(cr, uid, vals, context=context)
                # 计算费用合计：代理费总额+定金
                sum_agent = 0
                for line in obj.order_line:
                    sum_agent += line.agency_amount
                val = {}
                val['order_id'] = res_id
                val['date'] = datetime.now().date()
                val['partner_id'] = obj.agent_id.id
                val['amount_currency'] = obj.margin_rate_money
                val['communication'] = obj.name
                val['bank_id'] = self.get_partner_bank(cr, uid, ids, obj.agent_id.id)
                val['communication2'] = "委托协议定金"
                val['name'] = obj.pool.get('ir.sequence').get(cr, uid, 'payment.line')
                val['state'] = 'normal'
                val['currency'] = obj.company_id.currency_id.id
                if obj.margin_rate_money:
                    payment_line_obj.create(cr, uid, val, context=None)
                    res_lst.append(res_id)
                if not obj.margin_log and sum_agent:
                    new_id = payment_obj.copy(cr, uid, res_id)
                    val['order_id'] = new_id
                    val['invoice_id'] = account_id[0]
                    val['amount_currency'] = sum_agent
                    val['communication2'] = "服务费"
                    val['name'] = obj.pool.get('ir.sequence').get(cr, uid, 'payment.line')
                    val['currency'] = obj.company_id.currency_id.id
                    payment_line_obj.create(cr, uid, val, context=None)
                    res_lst.append(new_id)
                if not obj.margin_rate_money:
                    payment_obj.unlink(cr, uid, res_id)
                return res_lst
        if context.get('default_model') == 'redeem_id':
            obj = redeem_obj.browse(cr, uid, ids[0])
            vals['payment_supplier'] = obj.partner_id.id
        return [res_id]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: