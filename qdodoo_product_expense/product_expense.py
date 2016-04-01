# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Autor:Kevin Kong (kfx2007@163.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, models, _, fields
from openerp import workflow
from openerp.exceptions import except_orm
import datetime


class product_expense(models.Model):
    _name = 'product.expense'
    _inherit = ['mail.thread']

    name = fields.Char('Name', readonly=True)
    staff = fields.Many2one('hr.employee', 'Employee', required=True)
    department = fields.Many2one('hr.department', 'Department')
    date = fields.Date('Date')
    expense_line = fields.One2many('product.expense.line', 'expense_id', 'Products',
                                   states={'draft': [('readonly', False)], 'confirm': [('readonly', True)],
                                           'accepted': [('readonly', True)], 'waiting': [('readonly', True)],
                                           'done': [('readonly', True)], 'refused': [('readonly', True)]})
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('accepted', 'Accepted'), ('waiting', 'Waiting'),
                   ('done', 'Done'), ('refused', 'Refused')], string="Status", track_visibility='onchange')
    amount = fields.Float('Amount', compute="_get_amount")
    note = fields.Text('Free Notes')
    ref_no = fields.Many2one('stock.picking', 'Ref Delivery', readonly=True)
    procurement_group = fields.Many2one('procurement.group', 'Procurement group', copy=False)
    usage = fields.Many2one('product.expense.usage', 'Usage', required=True)
    expense_location = fields.Many2one('stock.location', u'费用库位', domain=[('usage', '=', 'internal')],
                                       required=True)
    warehouse = fields.Many2one('stock.warehouse', u'仓库', required=True)
    analytic_acc = fields.Many2one('account.analytic.account', u'辅助核算')
    company_id = fields.Many2one('res.company', u'当前登录人所属公司')

    def change_location_id(self, cr, uid, ids, location_id, context=None):
        if location_id:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, location_id, context=context)
            return {'value': {'expense_location': warehouse.lot_stock_id.id}}
        return {}

    def get_company_id(self, cr, uid, ids, context=None):
        return self.pool.get('res.users').browse(cr, uid, uid).company_id.id

    _defaults = {
        'company_id': get_company_id,
    }

    @api.one
    def _get_amount(self):
        for line in self.expense_line:
            self.amount += line.subtotal

    def action_confirm(self):
        self.state = 'confirm'

    def action_accept(self):
        self.state = 'accepted'

    def action_refuse(self):
        self.state = 'refused'

    def do_transfer(self):
        if self.on_ship_create():
            self.state = 'waiting'

    def _prepare_procurement_group(self):
        return {'name': self.name, 'partner_id': self.staff.address_home_id.id}

    def _prepare_expense_line_procurement(self, line, group):
        expense_loc = self.env['stock.location'].search([('expense_location', '=', True)])
        # find suitalbe route for specified department
        rule_id = self.env['procurement.rule'].search([('location_id', '=', expense_loc.id), (
            'location_src_id', '=', self.expense_location.id),
                                                       ('warehouse_id', '=', self.warehouse.id)])
        return {
            "name": self.name,
            "origin": self.name,
            "date_planed": datetime.datetime.now(),
            "product_id": line.product.id,
            "product_qty": line.quantity,
            "product_uom": line.price_unit.id,
            "product_uos_qty": line.quantity,
            "proudct_uos": line.price_unit.id,
            "group_id": group,
            "invoice_state": "none",
            "expense_line_id": line.id,
            "location_id": expense_loc.id,
            "partner_dest_id": self.staff.address_home_id.id,
            "rule_id": rule_id.id,
        }

    @api.model
    def on_ship_create(self):
        # new version using procurement to create shipping
        procurement_obj = self.env['procurement.order']
        expense_line_obj = self.env['product.expense.line']
        # proc_ids=[]
        vals = self._prepare_procurement_group()
        if not self.procurement_group and len(vals):
            self.procurement_group = self.env['procurement.group'].create(vals)
        for line in self.expense_line:
            if line.procurement_ids:
                procurement_obj.check([x.id for x in line.procurement_ids if x.state not in ['cancel', 'done']])
                line.refresh()
                for x in line.procurement_ids:
                    if x.state in ('exception', 'cancel'):
                        x.reset_to_confirmed()
                        # procurement_obj.reset_to_confirmed(proc_ids)
            elif line.need_procurement():
                # if line.state=='done' or not line.product:
                #    continue
                vals = self._prepare_expense_line_procurement(line, self.procurement_group.id)
                proc_id = procurement_obj.create(vals)
                proc_id.run()
                # proc_ids.append(proc_id)
                # procurement_obj.run(proc_ids)
        return True

    @api.one
    @api.constrains('expense_line')
    def _check_expense_line(self):
        if not len(self.expense_line):
            raise except_orm(_('Warning!'), _('You must add at least one product!'))

    def create(self, cr, uid, vals, context=None):
        uid = 1
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'product.expense')
        expense_id = self.pool.get('stock.location').search(cr, uid, [('expense_location', '=', True)])
        expense_loc = self.pool.get('stock.location').browse(cr, uid, expense_id[0])
        res = super(product_expense, self).create(cr, uid, vals, context=context)
        res_obj = self.pool.get("product.expense").browse(cr, uid, res)
        pull_obj = self.pool.get('procurement.rule')
        if not pull_obj.search(cr, uid,
                               [('location_id', '=', expense_loc.id), ('warehouse_id', '=', res_obj.warehouse.id)]):
            pull_obj.create(cr, uid, {'name': 'Expense Route → ' + res_obj.warehouse.name,
                                      'location_id': expense_loc.id,
                                      'warehouse_id': res.warehouse.id,
                                      'procure_method': 'make_to_stock',
                                      'action': 'move',
                                      'picking_type_id': res_obj.warehouse.out_type_id.id,
                                      'location_src_id': res_obj.expense_location.id,
                                      })
        return res

    @api.multi
    def write(self, vals):
        expense_loc = self.env['stock.location'].search([('expense_location', '=', True)])
        res = super(product_expense, self).write(vals)
        warehouse = vals.get('warehouse') or False
        location = vals.get('expense_location') or False
        route = self.env['procurement.rule'].search(
            [('location_id', '=', expense_loc.id), ('warehouse_id', '=', self.warehouse.id)])
        if route:
            if warehouse:
                route.write({'warehouse_id': warehouse})
            if location:
                route.write({'location_src_id': location})
        else:
            # create new expense route
            pull_obj = self.env['procurement.rule']
            pull_obj.create({'name': 'Expense Route → ' + self.warehouse.name,
                             'location_id': expense_loc.id,
                             'warehouse_id': self.warehouse.id,
                             'procure_method': 'make_to_stock',
                             'action': 'move',
                             'picking_type_id': self.warehouse.out_type_id.id,
                             'location_src_id': self.expense_location.id,
                             })

        return res

    @api.onchange('staff')
    def _onchange_staff(self):
        self.department = self.staff.department_id

    @api.one
    def copy(self):
        p = super(product_expense, self).copy()
        p.ref_no = None
        p.expense_line = self.expense_line.copy()
        p.state = 'draft'
        return p

    def do_ship_end(self):
        self.write({'state': 'done'})
        account_obj = self.env['account.move']
        account_moves = account_obj.search([('ref', '=', self.ref_no.name)])
        for line in self.expense_line:
            if len(account_moves):
                for account_move in account_moves:
                    for a_line in account_move.line_id:
                        if a_line.product_id == line.product and a_line.credit != 0 and a_line.debit == 0:
                            a_line.write({'account_id': self.usage.debit.id})
                        if a_line.product_id == line.product and a_line.debit != 0 and a_line.credit == 0:
                            a_line.write({'account_id': self.usage.credit.id,
                                          'analytic_account_id': self.analytic_acc.id})


class product_expense_line(models.Model):
    _name = "product.expense.line"

    expense_id = fields.Many2one('product.expense', 'Expense_id')
    product = fields.Many2one('product.product', 'Product', domain=[('hr_expense_ok', '=', True)])
    expense_date = fields.Date('Expense Date')
    comment = fields.Char('Comment')
    price_unit = fields.Many2one('product.uom', 'Unit')
    price = fields.Float('Price')
    quantity = fields.Float('Quantity')
    subtotal = fields.Float('Subtotal', compute='_get_subtotal')
    procurement_ids = fields.One2many('procurement.order', 'expense_line_id', 'Expense Procurement')

    @api.one
    def need_procurement(self):
        product = self.env['product.product'].browse(self.product.id)
        if product.need_procurement():
            return True
        return False

    @api.onchange('quantity')
    def _onchange_quantity(self):
        self.subtotal = self.price * self.quantity

    @api.onchange('price')
    def _onchange_price(self):
        self.subtotal = self.price * self.quantity

    @api.one
    def _get_subtotal(self):
        self.subtotal = self.price * self.quantity

    @api.onchange('product')
    def _onchange_product(self):
        self.price_unit = self.product.uom_id
        self.price = self.product.standard_price

    @api.constrains('quantity', 'price')
    def _check_quantity_price(self):
        if self.quantity == 0 or self.price == 0:
            raise except_orm(_('Warning!'), _('The Quantity Or Price Can not be Zero!'))

    @api.model
    def create(self, val):
        if not val.get('price'):
            val['price'] = self.env['product.product'].browse(val['product']).standard_price
        return super(product_expense_line, self).create(val)


class product_expense_picking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    def do_transfer(self):
        res = super(product_expense_picking, self).do_transfer()
        if res:
            expense = self.env['product.expense'].search([('name', '=', self.origin)])
            if expense:
                for line in expense:
                    line.ref_no = self.id
                    workflow.trg_validate(self.env.user.id, 'product.expense', line.id, 'ship_end', self.env.cr)
        return res


class procurement_order(models.Model):
    _inherit = 'procurement.order'

    expense_line_id = fields.Many2one('product.expense.line', 'Product Expense Line')


class stock_location(models.Model):
    _inherit = 'stock.location'

    expense_location = fields.Boolean('Expense Location')
