# -*- coding: utf-8 -*-
###########################################################################################
#
#    account.moves.report for Odoo8.0
#    Copyright (C) 2016 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import tools
from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp


class account_moves_report(osv.osv):
    _name = "account.moves.report"
    _description = u"会计分录明细统计报表"
    _auto = False  #不创建数据库，由init方法中的SQL语句初始化数据
    _rec_name = 'date'
    _columns = {
        'date': fields.date(u'实际日期', readonly=True),  # TDE FIXME master: rename into date_effective
        'date_created': fields.date(u'创建日期', readonly=True),
        'date_maturity': fields.date(u'成熟日期', readonly=True),
        'ref': fields.char(u'参考', readonly=True),
        'nbr': fields.integer(u'# 项目', readonly=True),
        'debit': fields.float(u'借方', readonly=True, digits=(20, 4)),  #digits：数字总长度和小数精度
        'credit': fields.float(u'贷方', readonly=True, digits=(20, 4)),
        'balance': fields.float(u'余额', readonly=True, digits=(20, 4)),
        'currency_id': fields.many2one('res.currency', u'币种', readonly=True),
        'amount_currency': fields.float(u'总额外币', digits_compute=dp.get_precision('Account'), readonly=True),
        'period_id': fields.many2one('account.period', u'会计期间', readonly=True),
        'account_id': fields.many2one('account.account', u'科目', readonly=True),
        'journal_id': fields.many2one('account.journal', u'分类账', readonly=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', u'会计年度', readonly=True),
        'product_id': fields.many2one('product.product', u'产品', readonly=True),
        'product_uom_id': fields.many2one('product.uom', u'产品计量单位', readonly=True),
        'move_state': fields.selection([('draft',u'未登帐'), ('posted',u'已登帐')], u'状态', readonly=True),
        'move_line_state': fields.selection([('draft',u'未平衡'), ('valid',u'有效')], u'分录行的状态', readonly=True),
        'reconcile_id': fields.many2one('account.move.reconcile', u'调节号码', readonly=True),
        'partner_id': fields.many2one('res.partner',u'业务伙伴', readonly=True),
        'analytic_account_id': fields.many2one('account.analytic.account', u'分析账户', readonly=True),
        'quantity': fields.float(u'产品数量', digits=(16,2), readonly=True),  # TDE FIXME master: rename into product_quantity
        'user_type': fields.many2one('account.account.type', u'科目类型', readonly=True),
        'type': fields.selection([
            ('receivable', u'应收'),
            ('payable', u'应付'),
            ('cash', u'现金'),
            ('view', u'视图'),
            ('consolidation', u'合并'),
            ('other', u'常规科目'),
            ('closed', u'已关闭'),
        ], u'内部类型', readonly=True, help="这种类型是用来区分Odoo的特殊效果：视图不能拥有实例，整个那些拥有多公司子账户的账户，因折旧账户而关闭..."),
        'company_id': fields.many2one('res.company', u'公司', readonly=True),
    }

    _order = 'date desc'

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        for arg in args:
            if arg[0] == 'period_id' and arg[2] == 'current_period':
                current_period = period_obj.find(cr, uid, context=context)[0]
                args.append(['period_id','in',[current_period]])
                break
            elif arg[0] == 'period_id' and arg[2] == 'current_year':
                current_year = fiscalyear_obj.find(cr, uid)
                ids = fiscalyear_obj.read(cr, uid, [current_year], ['period_ids'])[0]['period_ids']
                args.append(['period_id','in',ids])
        for a in [['period_id','in','current_year'], ['period_id','in','current_period']]:
            if a in args:
                args.remove(a)
        return super(account_moves_report, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order,
            context=context, count=count)

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False,lazy=True):
        if context is None:
            context = {}
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        if context.get('period', False) == 'current_period':
            current_period = period_obj.find(cr, uid, context=context)[0]
            domain.append(['period_id','in',[current_period]])
        elif context.get('year', False) == 'current_year':
            current_year = fiscalyear_obj.find(cr, uid)
            ids = fiscalyear_obj.read(cr, uid, [current_year], ['period_ids'])[0]['period_ids']
            domain.append(['period_id','in',ids])
        else:
            domain = domain
        return super(account_moves_report, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby,lazy)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_moves_report')
        cr.execute("""
            create or replace view account_moves_report as (
            select
                l.id as id,
                am.date as date,
                l.date_maturity as date_maturity,
                l.date_created as date_created,
                am.ref as ref,
                am.state as move_state,
                l.state as move_line_state,
                l.reconcile_id as reconcile_id,
                l.partner_id as partner_id,
                l.product_id as product_id,
                l.product_uom_id as product_uom_id,
                am.company_id as company_id,
                am.journal_id as journal_id,
                p.fiscalyear_id as fiscalyear_id,
                am.period_id as period_id,
                l.account_id as account_id,
                l.analytic_account_id as analytic_account_id,
                a.type as type,
                a.user_type as user_type,
                1 as nbr,
                l.quantity as quantity,
                l.currency_id as currency_id,
                l.amount_currency as amount_currency,
                l.debit as debit,
                l.credit as credit,
                coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0) as balance
            from
                account_move_line l
                left join account_account a on (l.account_id = a.id)
                left join account_move am on (am.id=l.move_id)
                left join account_period p on (am.period_id=p.id)
                where l.state != 'draft'
            )
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
