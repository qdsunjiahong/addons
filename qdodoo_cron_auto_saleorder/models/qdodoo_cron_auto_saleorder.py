# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp.osv import osv, fields
import datetime
import urllib2
from lxml import etree
from openerp.tools.translate import _


class qdodoo_cron_saleorder(osv.Model):
    """
        北邮系统对接
    """
    _inherit = 'sale.order'  # 继承

    # 字段定义
    _columns={
        'is_auto':fields.boolean(string='自动创建'),
    }
    _defaults = {
        'is_auto':False,
    }
    # 定义方法
    # 自动执行的计划
    def start_update(self, cr, uid, yearsday=False, context=None):
        if not yearsday:
            # 得到昨天的日期
            yearsday = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')
        if not context:
            context = {}
        beiyou = self.pool.get('beiyou.data')
        # ==============================lxml方式=====================================
        # 测试url
        # html_url = r"http://221.215.106.214:8080/ci/webservices/index.php/api/b2test/order/sql/2015-02-01"
        # 正式url
        html_url = r"http://123.129.242.98:8080/bbw/webservices/index.php/api/b2erp/order/sql/" + yearsday
        # print html_url
        # 获得html工作流
        html_stream = urllib2.urlopen(html_url)
        # 解析xml
        doc = etree.parse(html_stream)
        # 获取根节点
        root = doc.getroot()
        # 遍历出所有item数据[{'vname':value},{}]
        data = []
        for item in root.getiterator('item'):
            data_dict = {}
            for it in item.getchildren():
                data_dict[it.tag] = it.text
            data.append(data_dict)

        is_havadata = beiyou.search(cr, uid, [('date', '=', yearsday)])
        message = ''
        if is_havadata:
            message += '今天已经插入北邮模型数据！\n'
        else:
            self.create_model_data(cr, uid, data, yearsday, context=context)
        search_notin_data = beiyou.search(cr, uid, [('is_save', '=', False)], context=context)
        if search_notin_data:
            self.input_data(cr, uid, search_notin_data, yearsday, context=context)
        else:
            message += '没有查到未插入的数据！\n'
        self.write_loggin_line(cr, uid, message)




    def input_data(self, cr, uid, data_list, order_date, context=None):
        partner = self.pool.get('res.partner')
        order = self.pool.get('sale.order.line')
        product = self.pool.get('product.product')
        stock = self.pool.get('stock.warehouse')
        error_model = self.pool.get('beiyou.data')
        for data in error_model.browse(cr, uid, data_list):
            message = '================================开始插入一条数据==============================\n'
            try:
                simple_message = '数据%s,%s,%s,%s,%s,%s:\n' % (
                data.vaname, data.housename, data.goodsno, data.product_name, data.number, data.total)
                total = float(data.total)
                number = float(data.number)
                partner_id = partner.search(cr, uid, [('name', '=', data.vaname)], context=context)
                if not partner_id:
                    simple_message += '没有%s这个供应商\n' % data.vaname
                    error_model.write(cr, uid, data.id, {'description': simple_message}, context=context)
                    continue
                stock_id = stock.search(cr, uid, [('name', '=', data.housename)], context=context)
                if not stock_id:
                    simple_message += '没有%s这个仓库\n' % data.housename
                    error_model.write(cr, uid, data.id, {'description': simple_message}, context=context)
                    continue
                product_id = product.search(cr, uid, [('default_code', '=', data.goodsno),
                                                          ('company_id', '=', 3)], context=context)
                if not product_id:
                    simple_message += '未查询到名称为%s内部编号为%！\n'%(data.product_name,data.goodsno)
                    error_model.write(cr, uid, data.id, {'description': simple_message}, context=context)
                    continue
                search_id = self.search(cr,uid,[('partner_id','in',partner_id),('company_id','=',3),('warehouse_id','in',stock_id),('date_order','=',order_date),('is_auto','=',True)])
                if search_id:
                    order_line_id = order.create(cr, uid, {'order_id': search_id[0],
                                                      'product_id': product_id[0],
                                                      'product_uom_qty': number,
                                                      'price_unit': total/number}, context=context)
                else:
                    order_id = self.create(cr, uid,
                                 {'partner_id': partner_id[0],'company_id':3, 'order_policy':'manual','warehouse_id': stock_id[0], 'date_order': order_date,'is_auto':True},
                                 context=context)
                    order_line_id = order.create(cr, uid, {'order_id': order_id,
                                                      'product_id': product_id[0],
                                                      'product_uom_qty': number,
                                                      'price_unit': total/number}, context=context)

                message += '订单明细创建成功！\n'
                error_model.write(cr, uid, data.id, {'is_save': True,'description': simple_message}, context=context)

            except Exception, e:
                message += 'input_data运行异常！错误原因%s\n' % e
                simple_message += '请确定数量在仓库允许范围内！\n'
                error_model.write(cr, uid, data.id, {'description': simple_message}, context={})
            finally:
                message += '================================操作结束==============================\n'
                self.write_loggin_line(cr, uid, message+simple_message)

    # 创建北邮模型数据记录
    def create_model_data(self, cr, uid, data_ids, order_date, context=None):
        message = ""
        error_model = self.pool.get('beiyou.data')
        message += '试图创建北邮模型!\n'
        for data in data_ids:
            error_id = error_model.create(cr, uid,
                                      {'vaname': data.get('vaname'),
                                       'housename': data.get('housename'),
                                       'goodsno': data.get('goodsno'),
                                       'product_name': data.get('product_name'),
                                       'product_price': data.get('product_price'),
                                       'number': data.get('number'),
                                       'total': data.get('total'), 'is_save': False, 'date': order_date}, context=context)
            if error_id:
                message += '北邮模型创建成功!\n'
            else:
                message += '北邮模型创建失败！\n'
        self.write_loggin_line(cr, uid, message)

    def write_loggin_line(self, cr, uid, message):
        try:
            dict = {}
            file = self.pool.get('ir.config_parameter').get_param(cr, uid, 'beiyou.data_loggin', dict)
            fobj = open(file, 'a')
            fobj.seek(fobj.tell(), 2)
            # print message
            fobj.write(message)
        except Exception, e:
            mess = message + '日志写入报错!%s' % e
            self.message_box(mess)

    def message_box(self, message):
        warning = {}
        warning = {
            'title': '警告!',
            'message': message,
        }
        return {'warning': warning}

    # 根据字典写数据日志

    def write_loggin(self, cr, uid, data, message):
        try:
            dict = {}
            FILE = self.pool.get('ir.config_parameter').get_param(cr, uid, 'beiyou.data_loggin', dict)
            # FILE = r'O:\qdodoo\odoo-8.0-20150319\openerp\addons\qdodoo_cron_auto_saleorder\data\write_data.txt'
            # print FILE
            fobj = open(FILE, 'a')
            # 追加当前数据写入
            fobj.seek(fobj.tell(), 2)
            fobj.write("============" + datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S') + '==================================\n')
            fobj.write("%s,在%s\n" % (message, data))
            fobj.write('=================================================\n')
        except Exception, e:
            warning = {
                'title': '警告',
                'message': '日志出错！'
            }
            return {'warning': warning}
        finally:
            fobj.close()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# 定义新的数据模型 用于保存 正确或错误的数据
class beiyou_data(osv.Model):
    _name = 'beiyou.data'

    _columns = {
        'vaname': fields.char(string='客户'),
        'housename': fields.char(string='仓库'),
        'goodsno': fields.char(string='物流编号'),
        'number': fields.char(string='数量'),
        'product_price': fields.char(string="产品单价"),
        'product_name': fields.char(string="产品名称"),
        'total': fields.char(string="产品总价"),
        'is_save': fields.boolean(string="是否已保存"),
        'date': fields.datetime(string='订单日期'),
        'description': fields.text(string='备注信息'),
        'get_date': fields.date(string='日期'),
    }
    def btn_search(self, cr, uid, ids, context=None):
        obj = self.pool.get('sale.order')
        obj.start_update(cr, uid, self.browse(cr, uid, ids[0]).get_date)
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_cron_auto_saleorder', 'qdodoo_beiyou_tree')
        view_id = result and result[1] or False
        result_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'qdodoo_cron_auto_saleorder', 'qdodoo_beiyou_form')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('北邮数据显示'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'beiyou.data',
              'type': 'ir.actions.act_window',
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
              }
