# -*- coding: utf-8 -*-

from openerp.osv import fields
from openerp.osv import osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import time
import datetime

class rain_cost_share(osv.osv):
    _name = 'rain.cost.share'
    _description = 'Cost Share'

    _columns = {
        'name': fields.char(u'标题'),
        'period_id': fields.many2one('account.period', string=u'会计区间', required=True),
        'date': fields.date(string=u'日期'),
        'begin_period_id': fields.many2one('account.period', required=True, string=u'开始的会计区间',
                                           help=u'本期的费用分摊的开始的会计区间,当"开始会计区间" 与"会计区间" 相同的时候,不会去追溯本期的期初结存与期初成本差异.'),
        'state': fields.selection(string=u'状态', selection=[('draft', u'未分摊'), ('partial', u'部分分摊'), ('done', u'完成')],
                                  help=u'"draft":费用都未分摊,"partial" : 部分产品的成本的费用被分摊s,"done":产品费用全部分摊'),
        'account_move_id': fields.many2one('account.move', string=u'分摊的会计凭证'),
        'line_ids': fields.one2many('rain.cost.share.line', 'cost_share_id', u'费用分摊项')
    }

    _defaults = {
        'name': '/',
        'state': 'draft',
        'date': fields.date.context_today,
    }

    _sql_constraints = [
        ('period_idbegin_period_id_uniq', 'unique(period_id, begin_period_id)', u'会计区间重复!'),
    ]

    def action_share(self,cr, uid, ids, *args):

        cost_share_obj = self.browse(cr, uid, ids[0])

        if cost_share_obj.period_id.id != cost_share_obj.begin_period_id.id:
            #查找上期的分摊的会计凭证
            t = time.strptime(cost_share_obj.period_id.date_start,'%Y-%m-%d')
            y,m,d = t[0:3]
            date_start = datetime.datetime(y,m,d)
            last_date = date_start +  datetime.timedelta(-10)
            last_period_id = self.pool.get('account.period').search(cr, uid, [('date_start','<',last_date),('date_stop','>',last_date)])
            last_rain_cost_share_obj_id = self.search(cr, uid, [('period_id','in',last_period_id),('begin_period_id','=',cost_share_obj.begin_period_id.id)])
            if len(last_rain_cost_share_obj_id) == 0:
                raise osv.except_osv(u'上期分摊未处理',u'长期分摊未处理')
            last_rain_cost_share_obj = self.browse(cr, uid, last_rain_cost_share_obj_id[0])
            if last_rain_cost_share_obj.account_move_id.state != "posted":
                raise osv.except_osv(u'上期的分摊会计凭证未记账',u'请检查上期的分摊会计凭证!'+last_rain_cost_share_obj.account_move_id.name)

        #all lines to share
        lines = self.pool.get('rain.cost.share.line').search(cr,uid,[('cost_share_id','in',ids)])
        purchase_ids = self.pool.get('account.account').search(cr, uid, [('code', '=', 1401)])
        cost_ids = self.pool.get('account.account').search(cr, uid, [('code', '=', 6401)])
        cost_difference_ids = self.pool.get('account.account').search(cr, uid, [('code', '=', 1404)])

        account_move_line_pool = self.pool.get('account.move.line')
        done_id = []
        exception_id = []

        for line_id in lines:
            line = self.pool.get('rain.cost.share.line').browse(cr,uid, line_id)
            if line.state == 'done':
                continue
            # 材料成本差异[1404]
            line_cost_share_args = {
                'name':'Cost Share',
                'quantity':0.0,
                'product_id': line.product_id.id,
                'debit': 0.0,
                'credit': 0.0,
                'account_id':cost_difference_ids[0],
                'move_id':cost_share_obj.account_move_id.id,
                'state': 'draft',
            }
            #主营业务成本[6401]
            line_main_cost_args = {
                'name':'Main Cost Share',
                'quantity':0.0,
                'product_id': line.product_id.id,
                'debit': 0.0,
                'credit': 0.0,
                'account_id':cost_ids[0],
                'move_id':cost_share_obj.account_move_id.id,
                'state': 'draft',
            }

            if line.difference_share == 0.0:
                done_id.append(line_id)
                continue
            if line.share_ratio > 1.0 or line.share_ratio < 0.0:
                exception_id.append(line_id)
                continue
            if line.difference_share < 0:
                line_cost_share_args.update({
                    'debit':abs(line.difference_share)
                })
                line_main_cost_args.update({
                    'credit':abs(line.difference_share)
                })

            elif line.difference_share > 0:
                line_cost_share_args.update({
                    'credit':line.difference_share
                })
                line_main_cost_args.update({
                    'debit':line.difference_share
                })

            account_move_line_pool.create(cr,uid,line_cost_share_args)
            account_move_line_pool.create(cr,uid,line_main_cost_args)
            done_id.append(line_id)
        if len(done_id)> 0:
            self.pool.get('rain.cost.share.line').write(cr,uid,done_id,{'state':'done'})
        if len(exception_id) > 0:
            self.pool.get('rain.cost.share.line').write(cr,uid,exception_id,{'state':'done'})
            self.write(cr, uid, ids, {'state':'partial'})
        else:
            self.write(cr, uid, ids, {'state':'done'})

    def on_change_period_id(self, cr, uid, ids, period_id):
        if period_id:
            period_obj = self.pool.get('account.period').browse(cr, uid, period_id)
            return {'value': {'name': period_obj.name + u'/成本分摊'}}
        return {}

    def create_cost_share_lines(self, cr, uid, vals, cost_share_id, context=None):
        # 获取当前会计区间 内的 所有的凭证( 科目 库存产品[1406], 发出产品[1407], 材料成本差异[1404])
        #入库
        purchase_ids = self.pool.get('account.account').search(cr, uid, [('code', '=', 1406)])
        #出库
        cost_ids = self.pool.get('account.account').search(cr, uid, [('code', '=', 1407)])
        #差异
        cost_difference_ids = self.pool.get('account.account').search(cr, uid, [('code', '=', 1404)])

        period_id = vals.get('period_id', False)
        begin_period_id = vals.get('begin_period_id',False)

        purchase_id = purchase_ids[0]
        cost_id = cost_ids[0]
        cost_difference_id = cost_difference_ids[0]

        if period_id:
            # 记账的凭证, 在库存产品 发出产品  和 材料差异   记账的  ,本期的
            args = [
                ('account_id', 'in', [purchase_id, cost_id, cost_difference_id]),
                ('period_id', '=', period_id),
                ('state','=','valid')
            ]
            account_move_line_ids = self.pool.get('account.move.line').search(cr, uid, args, context=context)
            product_move_array = {
            }
            for account_move_line_id in account_move_line_ids:
                account_move_line_obj = self.pool.get('account.move.line').browse(cr, uid, account_move_line_id, context)
                product_id = account_move_line_obj.product_id.id
                if product_id:
                    keys = product_move_array.keys()
                    if product_id not in keys:
                        product_move_array[product_id] = {
                            'product_id': product_id,
                            'in_quantity': 0.0,
                            'out_quantity': 0.0,
                            'cost_difference': 0.0,
                        }
                    #判断是哪个类型的科目
                    account_id = account_move_line_obj.account_id.id
                    if account_id == purchase_id:
                        #材料采购
                        product_move_array[product_id]['in_quantity'] += account_move_line_obj.quantity
                    if account_id == cost_id:
                        #主营成本
                        product_move_array[product_id]['out_quantity'] += account_move_line_obj.quantity
                    if account_id == cost_difference_id:
                        product_move_array[product_id][
                            'cost_difference'] += account_move_line_obj.debit - account_move_line_obj.credit

            #形成rain.cost.share.line
            keys = product_move_array.keys()
            for k in keys:
                rain_cost_array_line = product_move_array[k]
                #begin_surplus_quantity  期初
                begin_surplus_quantity = 0.0
                begin_cost_difference = 0.0

                if period_id != begin_period_id:
                    #当前会计区间 与  开始会计区间 不相同
                    begin_data = self._recursive_get_begin_data(cr, uid, product_id, begin_period_id, period_id)
                    if begin_data:
                        begin_surplus_quantity = begin_data['begin_surplus_quantity']
                        begin_cost_difference =  begin_data['begin_cost_difference']
                line_args = {
                    'product_id':rain_cost_array_line['product_id'],
                    'begin_surplus_quantity':begin_surplus_quantity,
                    'in_quantity':rain_cost_array_line['in_quantity'],
                    'out_quantity':rain_cost_array_line['out_quantity'],
                    'share_ratio':0.0,
                    'begin_cost_difference':begin_cost_difference,
                    'cost_difference':rain_cost_array_line['cost_difference'],
                    'difference_share':0.0,
                    'cost_share_id':cost_share_id,
                    'period_id':period_id
                }

                if line_args['begin_surplus_quantity'] + line_args['in_quantity'] != 0:
                    line_args['share_ratio'] = round(float(line_args['out_quantity'])/(line_args['begin_surplus_quantity'] + line_args['in_quantity']),4)
                    line_args['difference_share'] = (line_args['begin_cost_difference'] + line_args['cost_difference']) * line_args['share_ratio']

                #创建 line
                self.pool.get('rain.cost.share.line').create(cr, uid, line_args)

        else:
            #报错
            pass

    def _recursive_get_begin_data(self,cr,uid, product_id, begin_period_id, period_id):
        """

        :param cr:
        :param uid:
        :param product_id:
        :param begin_period_id:
        :param period_id:  当前的会计区间
        :return:
        """
        if period_id == begin_period_id:
            return False
        else:
            period_obj = self.pool.get('account.period').browse(cr,uid, period_id)
            t = time.strptime(period_obj.date_start,'%Y-%m-%d')
            y,m,d = t[0:3]
            date_start = datetime.datetime(y,m,d)
            last_date = date_start +  datetime.timedelta(-10)
            last_period_id = self.pool.get('account.period').search(cr, uid, [('date_start','<',last_date),('date_stop','>',last_date)])
            last_rain_line_id = self.pool.get('rain.cost.share.line').search(cr, uid, [('period_id','in',last_period_id)])
            if len(last_rain_line_id) > 0:
                last_rain_line_obj = self.pool.get('rain.cost.share.line').browse(cr,uid, last_rain_line_id[0])
                if last_rain_line_obj.product_id.id == product_id:
                    begin_surplus_quantity = last_rain_line_obj.begin_surplus_quantity+last_rain_line_obj.in_quantity-last_rain_line_obj.out_quantity
                    begin_cost_difference = 0.0
                    #通过会计凭证计算
                    if last_rain_line_obj.state == 'done':
                        begin_cost_difference  = last_rain_line_obj.begin_cost_difference+last_rain_line_obj.cost_difference-last_rain_line_obj.difference_share
                    else:
                        begin_cost_difference  = last_rain_line_obj.begin_cost_difference+last_rain_line_obj.cost_difference
                    return {
                        'begin_surplus_quantity':begin_surplus_quantity,
                        'begin_cost_difference':begin_cost_difference,
                    }

            return self._recursive_get_begin_data(cr, uid,product_id, begin_period_id,last_period_id[0])

    def _get_cost_deference(self,cr, uid, period_id, product_id):
        '''
            获取 该产品的 材料差异 该日期内的,
        :param cr:
        :param uid:
        :param period_id:
        :param product_id:
        :return:
        '''
        cost_deference = 0.0

    def create(self, cr, uid, vals, context=None):
        #检查上级是否完成 以及 相应的 凭证是否记账
        if vals.get('period_id', False) != vals.get('begin_period_id', False):
            period_obj = self.pool.get('account.period').browse(cr, uid, vals.get('period_id', False))
            #查找上期的分摊的会计凭证
            t = time.strptime(period_obj.date_start,'%Y-%m-%d')
            y,m,d = t[0:3]
            date_start = datetime.datetime(y,m,d)
            last_date = date_start +  datetime.timedelta(-10)
            last_period_id = self.pool.get('account.period').search(cr, uid, [('date_start','<',last_date),('date_stop','>',last_date)])
            last_rain_cost_share_obj_id = self.search(cr, uid, [('period_id','in',last_period_id),('begin_period_id','=',vals.get('begin_period_id', False))])
            if len(last_rain_cost_share_obj_id) == 0:
                raise osv.except_osv(u'没有上期的"成本分摊",请先建立上期的"成本分摊"')
            last_rain_cost_share_obj = self.browse(cr, uid, last_rain_cost_share_obj_id[0])
            if last_rain_cost_share_obj.state == 'draft':
                raise osv.except_osv(u'上期的 "成本分摊" 未分摊',u'请先分摊上期的分摊:'+last_rain_cost_share_obj.name)
            if last_rain_cost_share_obj.account_move_id.state != "posted":
                raise osv.except_osv(u'上期的分摊会计凭证未记账',u'请检查上期的分摊会计凭证!'+last_rain_cost_share_obj.account_move_id.name)

        # 创建相应的会计凭证(使用 其他账簿)
        journal_id = self.pool.get('account.journal').search(cr, uid, [('code', '=',u'杂项')])
        if len(journal_id) == 0:
            raise  osv.except_osv(u'"杂项账簿" 不存在',u'请 补充  该账簿 code为  杂项')
        account_move_args = {
            'journal_id': journal_id[0],
            'period_id': vals.get('period_id', False),
            'state': 'draft'
        }
        account_move_obj_id = self.pool.get('account.move').create(cr, uid, account_move_args, context=context)
        vals.update({
            'account_move_id':account_move_obj_id
        })

        #创建 成本分摊
        cost_share_id = super(rain_cost_share, self).create(cr, uid, vals, context)
        self.create_cost_share_lines(cr, uid, vals, cost_share_id, context)

        return cost_share_id


class rain_cost_share_line(osv.osv):
    _name = 'rain.cost.share.line'
    _description = 'Cost Share Line'
    _columns = {
        'name': fields.char(string=u'费用分摊项'),
        'product_id': fields.many2one('product.product', u'产品', required=True),

        'begin_surplus_quantity': fields.float(u'期初结存数量', digits=(16, 2)),
        'in_quantity': fields.float(u'本月入库数量', digits=(16, 2)),
        'out_quantity': fields.float(u'本月出库数量', digits=(16, 2)),

        'share_ratio': fields.float(u'分摊比例', digits=(16, 2)),

        'begin_cost_difference': fields.float(u'期初差异余额', digits_compute=dp.get_precision('Account')),
        'cost_difference': fields.float(u'本月差异余额', digits_compute=dp.get_precision('Account')),

        'difference_share': fields.float(u'分摊差异余额', digits_compute=dp.get_precision('Account')),

        'period_id': fields.many2one('account.period', string=u'会计区间'),

        'cost_share_id': fields.many2one('rain.cost.share', string=u'费用分摊'),
        'state' : fields.selection(string=u'状态', selection=[('draft', u'未分摊'), ('exception', u'不能分摊'), ('done', u'完成')])
    }

    _defaults ={
        'state': 'draft'
    }

rain_cost_share_line()