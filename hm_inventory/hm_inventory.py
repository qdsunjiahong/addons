#coding:utf-8

from openerp import fields,api,_,models
import xlrd,base64

class hm_inventory(models.Model):
    _inherit="stock.inventory"

    xls = fields.Binary('XLS')

    @api.one
    def btn_import(self):
        if self.xls:
            excel = xlrd.open_workbook(file_contents=base64.decodestring(self.xls))
            sheets = excel.sheets()
            inventory_obj_line = self.env['stock.inventory.line']
            for sheet in sheets:
                for row in range(2,sheet.nrows):
                    default_code = str(sheet.cell(row,0).value).split('.')[0]
                    products = self.env['product.product'].search([('default_code','=',default_code)])
                    if len(products):
							real_count = sheet.cell(row,2).value
							inventory_obj_line.create({
									"product_id":products[0].id,
									"product_uom_id":products[0].uom_id.id,
									"location_id":self.location_id.id,
									"product_qty":real_count,
									"inventory_id":self.id,
                                                                        "theoretical_qty":self.get_theoretical_qty(products[0].id)
									})
    def get_theoretical_qty(self,product):
        dom = [('location_id', 'child_of', self.location_id.id),('product_id','=', product)]
        quant_obj = self.env['stock.quant']
        quants = quant_obj.search(dom)
        tot_qty = 0
        for quant in quants:
            tot_qty = quant.qty
        return tot_qty
