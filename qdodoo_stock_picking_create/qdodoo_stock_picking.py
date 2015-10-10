# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, fields, api
from datetime import datetime


class qdodoo_stock_picking(models.Model):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                }
                if prod.packop_id:
                    prod.packop_id.with_context(no_recompute=True).write(pack_datas)
                    processed_ids.append(prod.packop_id.id)
                else:
                    pack_datas['picking_id'] = self.picking_id.id
                    packop_id = self.env['stock.pack.operation'].create(pack_datas)
                    processed_ids.append(packop_id.id)
        # Delete the others
        packops = self.env['stock.pack.operation'].search(
            ['&', ('picking_id', '=', self.picking_id.id), '!', ('id', 'in', processed_ids)])
        packops.unlink()

        # Execute the transfer of the picking  default_location_dest_id

        self.picking_id.do_transfer()
        location_model_cus, lo_id = self.env['ir.model.data'].get_object_reference('stock', 'stock_location_suppliers')
        location_model_cus2, lo_id2 = self.env['ir.model.data'].get_object_reference('stock',
                                                                                     'stock_location_customers')
        if self.picking_id.picking_type_id.default_location_src_id.id in (lo_id, lo_id2):
            onshipping_id = self.env['stock.invoice.onshipping'].create({'invoice_date': fields.date.today()})
            onshipping_id.create_invoice()
        elif self.picking_id.picking_type_id.default_location_dest_id.id in (lo_id, lo_id2):
            onshipping_id = self.env['stock.invoice.onshipping'].create({'invoice_date': fields.date.today()})
            onshipping_id.create_invoice()
        return True
