# -*- coding: utf-8 -*-

from openerp import models, api, _
from openerp.exceptions import Warning


class res_partner(models.Model):
    _inherit = "res.partner"

    @api.one
    @api.constrains('ref')
    def check_unique_partner_ref(self):
        if self.ref:
            filters = [('ref', '=', self.ref)]
            partner_ids = self.search(filters)
            if len(partner_ids) > 1:
                raise Warning(
                    _('供应商内部编号不允许重复,请检查修改!'))
