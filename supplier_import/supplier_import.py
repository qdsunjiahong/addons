# coding:utf-8

from openerp import fields, models, api, _
import xlrd, base64
import time


class supplier_import(models.Model):
    _name = "supplier.import"

    xls = fields.Binary('Excel File')
    customer = fields.Boolean('Customer')

    @api.multi
    def btn_import(self):
        supplier_obj = self.env['res.partner']
        return_list = []
        view_model, view_id = self.env['ir.model.data'].get_object_reference('base', 'view_partner_tree')
        view_form_model, view_form_id = self.env['ir.model.data'].get_object_reference('base', 'view_partner_form')
        if self.xls:
            excel = xlrd.open_workbook(file_contents=base64.decodestring(self.xls))
            sheets = excel.sheets()
            for sh in sheets:
                for row in range(3, sh.nrows):
                    # if customer or supplier
                    if self.customer:
                        data = {
                            'name': sh.cell(row, 2).value and str(sh.cell(row, 2).value) or '',
                            'phone': sh.cell(row, 3).value and str(sh.cell(row, 3).value) or '',
                            'mobile': sh.cell(row, 4).value and str(sh.cell(row, 4).value) or '',
                            'email': sh.cell(row, 5).value and str(sh.cell(row, 5).value) or '',
                            'ref': sh.cell(row, 6).value and str(sh.cell(row, 6).value) or '',
                            'contact': sh.cell(row, 7).value and str(sh.cell(row, 7).value) or '',
                            'credit_limit': sh.cell(row, 8).value and float(sh.cell(row, 8).value) or 0,
                            'comment': sh.cell(row, 9).value and str(sh.cell(row, 9).value) or '',
                            'customer': True,
                        }
                        if str(sh.cell(row, 0)) in ('Y', 'y'):
                            data['is_company'] = True
                        if str(sh.cell(row, 1)) in ('y', 'Y'):
                            data['is_internal'] = True
                        if sh.cell(row, 11).value:
                            try:
                                company_id = self.env['res.company'].search(
                                    [('name', '=', str(sh.cell(row, 11).value))]).id
                                data['company_id'] = company_id
                            except:
                                pass
                        if sh.cell(row, 10).value:
                            try:
                                addr_list = sh.cell(row, 10).value.split('/')
                                country_id = self.env['res.country'].search(
                                    [('name', '=', addr_list[0])]).id or False
                                state_id = self.env['res.country.state'].search(
                                    [('name', '=', addr_list[1])]).id or False
                                city = self.env['hm.city'].search([('name', '=', addr_list[2])]).id or False
                                street = addr_list[3]
                                data['country_id'] = country_id
                                data['state_id'] = state_id
                                data['city'] = city
                                data['street'] = street
                            except:
                                pass
                    else:
                        data = {
                            'name': sh.cell(row, 2).value and str(sh.cell(row, 2).value) or '',
                            'phone': sh.cell(row, 3).value and str(sh.cell(row, 3).value) or '',
                            'mobile': sh.cell(row, 4).value and str(sh.cell(row, 4).value) or '',
                            'email': sh.cell(row, 5).value and str(sh.cell(row, 5).value) or '',
                            'ref': sh.cell(row, 6).value and str(sh.cell(row, 6).value) or '',
                            'contact': sh.cell(row, 7).value and str(sh.cell(row, 7).value) or '',
                            'credit_limit': sh.cell(row, 8).value and float(sh.cell(row, 8).value) or 0,
                            'comment': sh.cell(row, 9).value and str(sh.cell(row, 9).value) or '',
                            'supplier': True,
                        }
                        if str(sh.cell(row, 0)) in ('Y', 'y'):
                            data['is_company'] = True
                        if str(sh.cell(row, 1)) in ('y', 'Y'):
                            data['is_internal'] = True
                        if sh.cell(row, 11).value:
                            try:
                                company_id = self.env['res.company'].search(
                                    [('name', '=', str(sh.cell(row, 11).value))]).id
                                data['company_id'] = company_id
                            except:
                                pass
                        if sh.cell(row, 10).value:
                            try:
                                addr_list = sh.cell(row, 10).value.split('/')
                                country_id = self.env['res.country'].search(
                                    [('name', '=', addr_list[0])]).id or False
                                state_id = self.env['res.country.state'].search(
                                    [('name', '=', addr_list[1])]).id or False
                                city = self.env['hm.city'].search([('name', '=', addr_list[2])]).id or False
                                street = addr_list[3]
                                data['country_id'] = country_id
                                data['state_id'] = state_id
                                data['city'] = city
                                data['street'] = street
                            except:
                                pass
                    crea_obj = supplier_obj.create(data)
                    return_list.append(crea_obj.id)
            return {
                'name': _(u'供应商'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'res.partner',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', return_list)],
                'views': [(view_id, 'tree'), (view_form_id, 'form')],
                'view_id': [view_id],
            }


class customer(models.Model):
    _inherit = 'res.partner'

    contact = fields.Char(string=u'联系人')
