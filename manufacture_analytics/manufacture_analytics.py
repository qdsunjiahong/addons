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

from openerp import fields, api, _, models
import logging

_logger = logging.getLogger(__name__)


class manufacture_analytics(models.Model):
    _inherit = "mrp.production"

    analytic_account = fields.Many2one('account.analytic.account', 'Analytics Account')

    @api.one
    def action_production_end(self):
        accout_move_line_obj = self.env['account.move.line']
        lines = accout_move_line_obj.search([('name', '=', self.name)])
        if len(lines):
            for line in lines:
                line.analytic_account_id = self.analytic_account.id
        return super(manufacture_analytics, self).action_production_end()


    def update_old_data(self, cr, uid, ids):
        accout_move_line_obj = self.pool.get('account.move.line')
        mrp_production_obj = self.pool.get('mrp.production')
        sql = """select aml.id,aal.account_id,aml.name from account_move_line aml LEFT JOIN account_analytic_line aal ON aal.move_id = aml.id where aml.name like 'MO%'"""
        cr.execute(sql.decode('utf-8'))
        result = cr.fetchall()
        _logger.debug('11111111111111111111111111 %s', result)
        count = 0
        for line in result:
            if line[1]:
                count += 1
                _logger.debug('22222222222222222222222222222 %s', count)
                _logger.debug('444444444444444444444444444444 %s', line[0])
                accout_move_line_obj.write(cr, uid, line[0], {'analytic_account_id':line[1]})
                mrp_ids = mrp_production_obj.search(cr, uid, ['name','=',line[2]])
                _logger.debug('333333333333333333333333333333 %s', mrp_ids)
                mrp_production_obj.write(cr, uid, mrp_ids, {'analytic_account':line[1]})
    # def update_old_data(self, cr, uid):
    #     accout_move_line_obj = self.pool.get('account.move.line')
    #     mrp_production_obj = self.pool.get('mrp.production')
    #     mrp_production_ids = mrp_production_obj.search(cr, uid, [])
    #     for mrp_production_id in mrp_production_obj.browse(cr, uid, mrp_production_ids):
    #         accout_move_line_ids = accout_move_line_obj.search(cr, uid, [('name', '=', mrp_production_id.name)])
    #         if accout_move_line_ids:
    #             for accout_move_line_id in accout_move_line_obj.browse(cr, uid, accout_move_line_ids):
    #                 fzhs = ''
    #                 # 获取对应的辅助核算项
    #                 for line_id in accout_move_line_id.analytic_lines:
    #                     fzhs = line_id.account_id.id
    #                     break
    #                 if not accout_move_line_id.analytic_account_id and fzhs:
    #                     accout_move_line_obj.write(cr, uid, accout_move_line_id.id,
    #                                                {'analytic_account_id': fzhs})
    #                 if not mrp_production_id.analytic_account and fzhs:
    #                     mrp_production_obj.write(cr, uid, mrp_production_id.id, {'analytic_account':fzhs})
    #     return True