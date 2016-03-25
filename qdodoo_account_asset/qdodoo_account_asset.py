# -*- coding: utf-8 -*-
###########################################################################################
#
#    author:Qdodoo suifeng
#    module name for Qdodoo
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import time


class qdodoo_account_asset(models.Model):
    """
        继承修改固定资产模块功能
    """
    _inherit = 'account.asset.asset'

    # 生成折旧板中数据的时候，按照采购日期的下月初开始
    def compute_depreciation_board(self, cr, uid, ids, context=None):
        # 折旧板模型
        depreciation_lin_obj = self.pool.get('account.asset.depreciation.line')
        for asset in self.browse(cr, uid, ids, context=context):
            # 如果剩余价值为空，跳出循环
            if asset.value_residual == 0.0:
                continue
            # 查询是否有已登账的折旧板
            posted_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_check', '=', True)],order='depreciation_date desc')
            # 查询是否有未登账的折旧板
            old_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_id', '=', False)])
            # 删除未登账的明细
            if old_depreciation_line_ids:
                depreciation_lin_obj.unlink(cr, uid, old_depreciation_line_ids, context=context)
            # 获取剩余价格
            amount_to_depr = residual_amount = asset.value_residual
            # 如果是年限百分比
            if asset.prorata:
                depreciation_date = datetime.strptime(self._get_last_depreciation_date(cr, uid, [asset.id], context)[asset.id], '%Y-%m-%d')
            else:
                # depreciation_date = 1st January of purchase year
                purchase_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d')
                #if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
                if (len(posted_depreciation_line_ids)>0):
                    last_depreciation_date = datetime.strptime(depreciation_lin_obj.browse(cr,uid,posted_depreciation_line_ids[0],context=context).depreciation_date, '%Y-%m-%d')
                    depreciation_date = (last_depreciation_date+relativedelta(months=+asset.method_period))
                else:
                    # -----odoo
                    # depreciation_date = datetime(purchase_date.year, 1, 1)
                    # ----suifeng
                    if purchase_date.month == 12:
                        depreciation_date = datetime(purchase_date.year+1, 1, 1)
                    else:
                        depreciation_date = datetime(purchase_date.year, purchase_date.month+1, 1)
                    # -------
            # 获取年月日、时分秒
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366

            undone_dotation_number = self._compute_board_undone_dotation_nb(cr, uid, asset, depreciation_date, total_days, context=context)
            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                i = x + 1
                amount = self._compute_board_amount(cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=context)
                residual_amount -= amount
                vals = {
                     'amount': amount,
                     'asset_id': asset.id,
                     'sequence': i,
                     'name': str(asset.id) +'/' + str(i),
                     'remaining_value': residual_amount,
                     'depreciated_value': (asset.purchase_value - asset.salvage_value) - (residual_amount + amount),
                     'depreciation_date': depreciation_date.strftime('%Y-%m-%d'),
                }
                depreciation_lin_obj.create(cr, uid, vals, context=context)
                # Considering Depr. Period as months
                depreciation_date = (datetime(year, month, day) + relativedelta(months=+asset.method_period))
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year
        return True

class qdodoo_account_asset_depreciation_line(models.Model):
    _inherit = 'account.asset.depreciation.line'

    # 修改生成会计凭证时日期为当月最后一天
    # 重新组织数据格式，合并生成凭证
    def create_move(self, cr, uid, ids, context=None):
        context = dict(context or {})
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        # 组织数据
        all_dict = {} # {日期(账期):{分类账：{资产obj:[line_obj]}}}
        for line in self.browse(cr, uid, ids, context=context):
            depreciation_date = context.get('depreciation_date') or line.depreciation_date or time.strftime('%Y-%m-%d')
            depreciation_date = depreciation_date[:8] + str(calendar.monthrange(int(depreciation_date[:4]),int(depreciation_date[5:7]))[1])
            context.update({'date': depreciation_date})
            if depreciation_date in all_dict:
                if line.asset_id.category_id.journal_id in all_dict[depreciation_date]:
                    if line.asset_id in all_dict[depreciation_date][line.asset_id.category_id.journal_id]:
                        all_dict[depreciation_date][line.asset_id.category_id.journal_id][line.asset_id].append(line)
                    else:
                        all_dict[depreciation_date][line.asset_id.category_id.journal_id][line.asset_id] = [line]
                else:
                    all_dict[depreciation_date][line.asset_id.category_id.journal_id] = {line.asset_id:[line]}
            else:
                all_dict[depreciation_date] = {line.asset_id.category_id.journal_id:{line.asset_id:[line]}}
        for key,value in all_dict.items():
            # 获取对应的账期
            period_ids = period_obj.find(cr, uid, key, context=context)
            for key1,value1 in value.items():
                # 根据账期、资产类别合并凭证明细
                journal_id = key1.id
                move_vals = {
                    'name': '/',
                    'date': key,
                    'ref': '合并凭证',
                    'period_id': period_ids and period_ids[0] or False,
                    'journal_id': journal_id,
                    }
                move_id = move_obj.create(cr, uid, move_vals, context=context)
                sign = (key1.type == 'purchase' and 1) or -1
                for key2,value2 in value1.items():
                    company_currency = key2.company_id.currency_id.id
                    current_currency = key2.currency_id.id
                    asset_name = key2.name
                    for line_obj in value2:
                        # 创建凭证明细行
                        reference = line_obj.name
                        amount = currency_obj.compute(cr, uid, current_currency, company_currency, line_obj.amount, context=context)
                        move_line_obj.create(cr, uid, {
                            'name': asset_name,
                            'ref': reference,
                            'move_id': move_id,
                            'account_id': key2.category_id.account_depreciation_id.id,
                            'debit': 0.0,
                            'credit': amount,
                            'period_id': period_ids and period_ids[0] or False,
                            'journal_id': journal_id,
                            'currency_id': company_currency != current_currency and current_currency or False,
                            'amount_currency': company_currency != current_currency and - sign * line_obj.amount or 0.0,
                            'date': key,
                        })
                        move_line_obj.create(cr, uid, {
                            'name': asset_name,
                            'ref': reference,
                            'move_id': move_id,
                            'account_id': key2.category_id.account_expense_depreciation_id.id,
                            'credit': 0.0,
                            'debit': amount,
                            'period_id': period_ids and period_ids[0] or False,
                            'journal_id': journal_id,
                            'currency_id': company_currency != current_currency and current_currency or False,
                            'amount_currency': company_currency != current_currency and sign * line_obj.amount or 0.0,
                            'analytic_account_id': key2.department.id,
                            'date': key,
                            'asset_id': key2.id
                        })
                        self.write(cr, uid, line_obj.id, {'move_id': move_id}, context=context)
                    asset_ids.append(key2.id)
                created_move_ids.append(move_id)

        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(cr, uid, list(set(asset_ids)), context=context):
            if currency_obj.is_zero(cr, uid, asset.currency_id, asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids