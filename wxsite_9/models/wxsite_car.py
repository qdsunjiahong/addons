# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
import xlrd,base64
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class qdodoo_wxsite_car(models.Model):
    _name = 'qdodoo.wxsite.car'

    name = fields.Many2one('product.template','产品')
    user_id = fields.Many2one('res.users',u'用户')
    number = fields.Integer(u'数量')

class qdodoo_pos_order_line_inherit(models.Model):
    _inherit = 'pos.order.line'

    is_make = fields.Boolean(u'是否制菜')
    is_out = fields.Boolean(u'是否传菜')

    _defaults = {
        'is_make':False,
        'is_out':False,
    }

class qdodoo_product_template_inherit(models.Model):
    _inherit = 'product.template'

    pos_sequence = fields.Integer(u'序列')
    is_meituan = fields.Boolean(u'美团产品')

class qdodoo_product_taste(models.Model):
    _name = 'qdodoo.product.taste'

    name = fields.Char(u'口味')

class qdodoo_print_list(models.Model):
   _name = 'qdodoo.print.list'

   name = fields.Char(u'信息')
   is_print = fields.Boolean(u'是否已打印')

class qdodoo_pos_config(models.Model):
    _inherit = 'pos.config'

    front_desk = fields.Char(u'前台打印机地址')
    send_desk = fields.Char(u'传菜台打印机地址')
    back_cook = fields.Char(u'后厨总单打印机地址')
    en_name = fields.Char(u'英文名称',required=True)
    order_name = fields.Char(u'最新编号')


class qdodoo_pos_order_inherit(models.Model):
    _inherit = 'pos.order'

    is_payment = fields.Boolean(u'是否已付款')

    _defaults = {
        'is_payment':False,
    }

    def write(self, cr, uid, ids, value, context={}):
        super(qdodoo_pos_order_inherit, self).write(cr, uid, ids, value, context=context)
        obj = self.browse(cr, uid, ids[0])
        if value.get('state') == 'paid' and obj.pos_reference:
            date_order = (datetime.strptime(obj.date_order,'%Y-%m-%d %H:%M:%S') + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
            # 组织后台打印数据
            infomation_new = """<receipt align="center" value-thousands-separator="" width="40">
                <div font="b">
                    <div size="double-height"><pre>订单号 %s</pre></div>
                    <div  size="double-height"><pre>%s</pre></div>
                </div>
                <div line-ratio="0.6">++++++"""%(obj.pos_reference,date_order)
            # 组织传菜台打印数据
            infomation_1 = """<receipt align="center" value-thousands-separator="" width="40">
                <div font="b">
                    <div size="double-height">传菜单</div>
                    <div size="double-height"><pre>订单号 %s</pre></div>
                    <div size="double-height"><pre>%s</pre></div>
                </div>
                <div line-ratio="0.6">++++++"""%(obj.pos_reference,date_order)
            # 后厨总单
            infomation_2 = """<receipt align="center" value-thousands-separator="" width="40">
                <div font="b">
                    <div size="double-height">后厨总单</div>
                    <div size="double-height"><pre>订单号 %s</pre></div>
                    <div  size="double-height"><pre>%s</pre></div>
                </div>
                <div line-ratio="0.6">++++++"""%(obj.pos_reference,date_order)
            printer_obj = self.pool.get('restaurant.printer')
            print_list_obj = self.pool.get('qdodoo.print.list')
            printer_ids = printer_obj.search(cr, 1, [])
            dict_ip = {}
            for printer_ids in printer_obj.browse(cr, 1, printer_ids):
                for line in printer_ids.product_categories_ids:
                    dict_ip[line.id] = printer_ids.proxy_ip
            for line in obj.lines:
                product_name = line.product_id.name
                if len(product_name) < 15:
                    product_name += ('　' * (15-len(product_name)))
                else:
                    product_name = product_name[:15]
                qty = str(line.qty)
                if len(qty) < 5:
                    qty += ('　' * (5-len(qty)))
                else:
                    qty = qty[:5]
                infomation_new += """<div size="double-height">
                    %s
                    %s
                    @@@@@%s@@@@@
                    </div>++++++"""%(product_name,qty,dict_ip.get(line.product_id.pos_categ_id.id))
                infomation_1 += """<div size="double-height">
                    %s
                    %s
                    @@@@@%s@@@@@
                    </div>++++++"""%(product_name,qty,obj.session_id.config_id.send_desk)
                infomation_2 += """<div size="double-height">
                    %s
                    %s
                    @@@@@%s@@@@@
                    </div>++++++"""%(product_name,qty,obj.session_id.config_id.back_cook)
            infomation_new += """</div>
                    <div size="double-height">
                        <left><pre>备注：%s号桌 %s</pre></left>
                    </div>
                    </receipt>"""%(obj.table_id.name, obj.note)
            infomation_1 += """</div>
                    <div size="double-height">
                        <left><pre>备注：%s号桌 %s</pre></left>
                    </div>
                    </receipt>"""%(obj.table_id.name, obj.note)
            infomation_2 += """</div>
                    <div size="double-height">
                        <left><pre>备注：%s号桌 %s</pre></left>
                    </div>
                    </receipt>"""%(obj.table_id.name, obj.note)
            print_list_obj.create(cr, 1, {'name':infomation_new,'is_print':False})
            print_list_obj.create(cr, 1, {'name':infomation_1,'is_print':False})
            print_list_obj.create(cr, 1, {'name':infomation_2,'is_print':False})
        return True

class qdodoo_pos_session_inherit(models.Model):
    _inherit = 'pos.session'

    def write(self, cr, uid, ids, value, context={}):
        super(qdodoo_pos_session_inherit, self).write(cr, uid, ids, value, context=context)
        obj = self.browse(cr, uid, ids[0])
        company = obj.user_id.company_id.name
        dict_all = {}
        all_num = 0
        all_amount = 0
        if value.get('state') == 'closed':
            stop_at = (datetime.strptime(obj.stop_at,'%Y-%m-%d %H:%M:%S') + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
            # 组织日结打印数据
            infomation_new = """<receipt align="center" value-thousands-separator="" width="40">
                <div font="b">
                    <div size="double-height"><pre>日结单</pre></div>
                    <div><pre>%s       %s</pre></div>
                    <div><pre>产品        数量        单价</pre></div>
                </div>
                <div line-ratio="0.6">++++++"""%(company, stop_at)

            for order in obj.order_ids:
                for line in order.lines:
                    all_num += line.qty
                    all_amount += line.qty * line.price_unit
                    if "['%s',%s]" % (line.product_id.name, line.price_unit) in dict_all:
                        dict_all["['%s',%s]" % (line.product_id.name, line.price_unit)] += line.qty
                    else:
                        dict_all["['%s',%s]" % (line.product_id.name, line.price_unit)] = line.qty

            for key, value in dict_all.items():
                product_name = eval(key)[0]
                if len(product_name) < 6:
                    product_name += ('　' * (6 - len(product_name)))
                else:
                    product_name = product_name[:6]
                qty = str(value)
                if len(qty) < 9:
                    qty += (' ' * (9 - len(qty)))
                else:
                    qty = qty[:9]
                price = str(eval(key)[1])
                if len(price) < 6:
                    price += (' ' * (6 - len(price)))
                else:
                    price = price[:6]

                infomation_new += """<div size="double-height">
                    %s
                    %s
                    %s
                    @@@@@%s@@@@@
                    </div>++++++""" % (product_name, qty, price, obj.config_id.front_desk)
            infomation_new += """</div>
                    <div>
                        <left><pre>数量: %s  总额：%s</pre></left>
                    </div>
                    </receipt>""" % (all_num, all_amount)
            print_list_obj = self.pool.get('qdodoo.print.list')
            print_list_obj.create(cr, 1, {'name':infomation_new,'is_print':False})
        return True

    def btn_day_end(self, cr, uid, ids, context={}):
        obj = self.browse(cr, uid, ids[0])
        company = obj.user_id.company_id.name
        dict_all = {}
        all_num = 0
        all_amount = 0
        stop_at = (datetime.strptime(obj.stop_at,'%Y-%m-%d %H:%M:%S') + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        # 组织日结打印数据
        infomation_new = """<receipt align="center" value-thousands-separator="" width="40">
            <div font="b">
                <div size="double-height"><pre>日结单</pre></div>
                <div><pre>%s       %s</pre></div>
                <div><pre>产品        数量        单价</pre></div>
            </div>
            <div line-ratio="0.6">++++++"""%(company, stop_at)

        # for line in obj.statement_ids:
        #     all_num += line.balance_end
        #     if line.journal_id in dict_all:
        #         dict_all[line.journal_id] += line.balance_end
        #     else:
        #         dict_all[line.journal_id] = line.balance_end

        for order in obj.order_ids:
            for line in order.lines:
                all_num += line.qty
                all_amount += line.qty*line.price_unit
                if "['%s',%s]"%(line.product_id.name,line.price_unit) in dict_all:
                    dict_all["['%s',%s]"%(line.product_id.name,line.price_unit)] += line.qty
                else:
                    dict_all["['%s',%s]"%(line.product_id.name,line.price_unit)] = line.qty

        for key, value in dict_all.items():
            product_name = eval(key)[0]
            if len(product_name) < 6:
                product_name += ('　' * (6-len(product_name)))
            else:
                product_name = product_name[:6]
            qty = str(value)
            if len(qty) < 9:
                qty += (' ' * (9-len(qty)))
            else:
                qty = qty[:9]
            price = str(eval(key)[1])
            if len(price) < 6:
                price += (' ' * (6-len(price)))
            else:
                price = price[:6]

            infomation_new += """<div size="double-height">
                %s
                %s
                %s
                @@@@@%s@@@@@
                </div>++++++"""%(product_name,qty,price,obj.config_id.front_desk)
        infomation_new += """</div>
                <div>
                    <left><pre>数量: %s  总额：%s</pre></left>
                </div>
                </receipt>"""%(all_num, all_amount)
        print_list_obj = self.pool.get('qdodoo.print.list')
        print_list_obj.create(cr, 1, {'name':infomation_new,'is_print':False})
        return True

class qdodoo_onchange_payment(models.Model):
    """
        修改支付方式
    """
    _name = 'qdodoo.onchange.payment'

    name = fields.Many2one('account.journal',u'新支付方式')

    @api.multi
    def btn_conformed(self):
        statement_line_obj = self.env['account.bank.statement.line']
        statement_obj = self.env['account.bank.statement']
        # 获取明细中原支付类型
        statement_id = statement_line_obj.browse(self._context.get('active_id'))
        old_journal = statement_id.journal_id
        if self.name != old_journal:
            # 获取新的结算单
            statement_id_obj = statement_obj.search([('state','=','open'),('journal_id','=',self.name.id)])
            if statement_id_obj:
                statement_id.write({'statement_id':statement_id_obj[0].id})
            else:
                raise osv.except_osv(_(u'警告'),_(u'缺少对应的银行对账单！'))

