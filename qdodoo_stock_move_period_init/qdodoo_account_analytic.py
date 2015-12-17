# encoding:utf-8
from openerp import models, fields, api


class qdodoo_stock_move_period_init(models.Model):
    _name = 'qdodoo.stock.move.period.init'

    @api.one
    def action_done(self):
        move_obj = self.env['stock.move']
        period_obj = self.env['account.period']
        move_ids = move_obj.search([('period_id', '=', False)])
        period_dict = {}
        period_dict_id = {}
        period_ids = period_obj.search([])
        for period_id in period_ids:
            company_id = period_id.company_id.id
            if company_id in period_dict:
                period_dict[company_id] += [(period_id.date_start + ' 00:00:01', period_id.date_stop + ' 23:59:59')]
            else:
                period_dict[company_id] = [(period_id.date_start + ' 00:00:01', period_id.date_stop + ' 23:59:59')]
            key_l = (period_id.date_start + ' 00:00:01', period_id.date_stop + ' 23:59:59', company_id)
            period_dict_id[key_l] = period_id.id
        for move_id in move_ids:
            for period_key in period_dict.get(move_id.company_id.id, []):
                if move_id.create_date >= period_key[0] and move_id.create_date <= period_key[1]:
                    move_id.write({'period_id': period_dict_id.get(period_key + (move_id.company_id.id,))})
