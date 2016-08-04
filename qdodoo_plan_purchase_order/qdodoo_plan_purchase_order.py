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

class qdodoo_plan_purchase_order(models.Model):
    """
        计划转采购单
    """
    _name = 'qdodoo.plan.purchase.order'    # 模型名称
    _description = 'qdodoo.plan.purchase.order'    # 模型描述
    _order = 'id desc'
    _inherit = ['mail.thread']

    name = fields.Char(u'单号',copy=False)
    location_name = fields.Many2one('stock.warehouse',u'仓库', required=True)
    company_id = fields.Many2one('res.company',u'公司')
    create_date_new = fields.Datetime(u'创建日期')
    minimum_planned_date = fields.Date(u'预计日期')
    location_id = fields.Many2one('stock.location',u'入库库位')
    order_line = fields.One2many('qdodoo.plan.purchase.order.line', 'order_id', u'产品明细',required=True)
    import_file = fields.Binary(string="导入的Excel文件")
    state = fields.Selection([('draft',u'草稿'),('sent',u'待确认'),('apply',u'待审批'),('confirmed',u'转换采购单'),('done',u'完成')],u'状态',track_visibility='onchange')
    origin = fields.Many2one('qdodoo.plan.purchase.order',u'源单据')
    notes = fields.Text(u'采购单号')
    notes_new = fields.Text(u'备注')
    product_manager_tfs = fields.Many2one('res.users',u'产品经理')


    _defaults = {
        'minimum_planned_date': datetime.now().date(),
        'create_date_new': datetime.now(),
        'state': 'draft',
        'company_id': lambda self, cr, uid, ids:self.pool.get('res.users').browse(cr, uid, uid).company_id.id,
    }

    # 退回
    def btn_cancel_confirmed(self, cr, uid, ids, context=None):
        line_lst = []
        log = 0
        all_line_lst = []
        for line in self.browse(cr, uid, ids[0]).order_line:
            all_line_lst.append(line.id)
            if line.is_cancel:
                line_lst.append(line.id)
            else:
                log += 1
        plan_line = self.pool.get('qdodoo.plan.purchase.order.line')
        if log:
            res_id = self.copy(cr, uid, ids[0],{'state':'sent','origin':ids[0]})
            for line_id in line_lst:
                plan_line.copy(cr, uid, line_id,{'order_id':res_id,'is_cancel':False})
            plan_line.unlink(cr, uid, line_lst)
            return True
        else:
            plan_line.write(cr, uid, all_line_lst, {'is_cancel':False})
            return self.write(cr, uid, ids, {'state':'sent'})

    # 退回
    def btn_cancel_draft(self, cr, uid, ids, context=None):
        line_lst = []
        log = 0
        all_line_lst = []
        for line in self.browse(cr, uid, ids[0]).order_line:
            all_line_lst.append(line.id)
            if line.is_cancel:
                line_lst.append(line.id)
            else:
                log += 1
        plan_line = self.pool.get('qdodoo.plan.purchase.order.line')
        if log:
            res_id = self.copy(cr, uid, ids[0],{'state':'draft','origin':ids[0]})
            for line_id in line_lst:
                plan_line.copy(cr, uid, line_id,{'order_id':res_id,'is_cancel':False})
            plan_line.unlink(cr, uid, line_lst)
            return True
        else:
            plan_line.write(cr, uid, all_line_lst, {'is_cancel':False})
            return self.write(cr, uid, ids, {'state':'draft'})

    # 退回
    def btn_cancel_approve(self, cr, uid, ids, context=None):
        line_lst = []
        log = 0
        all_line_lst = []
        for line in self.browse(cr, uid, ids[0]).order_line:
            all_line_lst.append(line.id)
            if line.is_cancel:
                line_lst.append(line.id)
            else:
                log += 1
        plan_line = self.pool.get('qdodoo.plan.purchase.order.line')
        if log:
            res_id = self.copy(cr, uid, ids[0],{'state':'apply','origin':ids[0]})
            for line_id in line_lst:
                plan_line.copy(cr, uid, line_id,{'order_id':res_id,'is_cancel':False})
            plan_line.unlink(cr, uid, line_lst)
            return True
        else:
            plan_line.write(cr, uid, all_line_lst, {'is_cancel':False})
            return self.write(cr, uid, ids, {'state':'apply'})

    # 导入方法
    def btn_import_data(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        if wiz.import_file:
            try:
                excel = xlrd.open_workbook(file_contents=base64.decodestring(wiz.import_file))
            except:
                raise osv.except_osv(_(u'提示'), _(u'请使用xls文件进行上传'))
            product_info = excel.sheet_by_index(0)
            product_obj = self.pool.get('product.product')
            purchase_line_obj = self.pool.get('qdodoo.plan.purchase.order.line')
            lst = []
            for obj in range(1, product_info.nrows):
                val = {}
                # 获取产品编号
                default_code = product_info.cell(obj, 0).value
                if not default_code:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品编号不能为空')%obj)
                # 获取计划日期
                if product_info.cell(obj, 2).value:
                    plan_date = datetime.strptime(product_info.cell(obj, 2).value, '%Y-%m-%d')
                else:
                    plan_date = datetime.now().date()
                # 获取产品数量
                product_qty = product_info.cell(obj, 3).value
                if not product_qty:
                    raise osv.except_osv(_(u'提示'), _(u'第%s行，产品数量不能为空')%obj)
                # 查询系统中对应的产品id
                product_id = product_obj.search(cr, uid,
                                                [('default_code', '=', default_code), ('company_id', '=', wiz.company_id.id)])
                if not product_id:
                    raise osv.except_osv(_(u'提示'), _(u'%s公司没有编号为%s的产品') % (wiz.company_id.name,default_code))
                product = product_obj.browse(cr, uid, product_id[0])
                val['product_id'] = product.id
                val['price_unit'] = product.standard_price
                val['name'] = product.name
                val['plan_date_jh'] = plan_date
                val['qty_jh'] = product_qty
                val['uom_id'] = product.uom_id.id
                val['order_id'] = wiz.id
                lst.append(val)
            for res in lst:
                purchase_line_obj.create(cr, uid, res)
            self.write(cr, uid, wiz.id, {'import_file': ''})
        else:
            raise osv.except_osv(_(u'提示'), _(u'请先上传模板'))

    # 获取序列号
    def create(self, cr, uid, vals, context=None):
        if not vals.get('name'):
            vals['name'] = self.pool.get('ir.sequence').get( cr, uid, 'qdodoo.plan.purchase.order')
        return super(qdodoo_plan_purchase_order, self).create(cr, uid, vals, context=context)

    # 获取目的库位
    def change_location_id(self, cr, uid, ids, location_id, context=None):
        if location_id:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, location_id, context=context)
            return {'value': {'location_id': warehouse.lot_stock_id.id}}
        return {}

    @api.multi
    # 提交
    def btn_draft_confirmed(self):
        dict_user = {} #{产品经理:[计划明细]}
        for line in self.order_line:
            line.write({'state':'sent'})
            if line.product_id.product_manager_tfs in dict_user:
                dict_user[line.product_id.product_manager_tfs].append(line)
            else:
                dict_user[line.product_id.product_manager_tfs] = [line]
        ids_list = []
        for key, value in dict_user.items():
            res_id = self.copy({'product_manager_tfs':key.id,'origin':'','notes':'','state':'sent'})
            for line_1 in value:
                line_1.write({'order_id':res_id.id})
            ids_list.append(res_id.id)
        self.unlink()
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_plan_purchase_order', 'view_tree_qdodoo_plan_purchase_order')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_plan_purchase_order', 'view_form_qdodoo_plan_purchase_order')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('计划转采购单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.plan.purchase.order',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',ids_list)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    # 确认
    def btn_confirmed(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('qdodoo.plan.purchase.order.line')
        line_id = line_obj.search(cr, uid, [('order_id','=',ids[0])])
        lines = line_obj.browse(cr, uid, line_id)
        #确认时验证是否无供应商信息
        for line in lines:
            if not line.partner_id:
                raise osv.except_osv(_(u'错误'), _(u'明细行无供应商信息，请修正！'))
        line_obj.write(cr, uid, line_id, {'state':'apply'})
        return self.write(cr, uid, ids, {'state':'apply'})

    # 审批
    def btn_approve(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('qdodoo.plan.purchase.order.line')
        line_id = line_obj.search(cr, uid, [('order_id','=',ids[0])])
        line_obj.write(cr, uid, line_id, {'state':'confirmed'})
        return self.write(cr, uid, ids, {'state':'confirmed'})

    # 转换采购单
    def btn_confirmed_done(self, cr, uid, ids, context=None):
        purchase_obj = self.pool.get('purchase.order')
        partner_obj = self.pool.get('res.partner')
        purchase_line_obj = self.pool.get('purchase.order.line')
        for obj in self.browse(cr, uid, ids):
            # 循环处理产品明细{(日期,供应商):[(产品,数量,单价,备注,单位id,产品经理)]}
            purchase_id = {}
            for line in obj.order_line:
                # 组织采购订单数据
                # 判断是否是同一到货日期和供应商
                if (line.plan_date,line.partner_id.id) in purchase_id:
                    # 如果存在重复的产品
                    all = purchase_id[(line.plan_date,line.partner_id.id)][:]
                    log = False
                    for key in all:
                        if line.product_id.id == key[0]:
                            log = True
                            key_new = key
                            purchase_id[(line.plan_date,line.partner_id.id)].remove(key)
                            # if line.qty_jh > line.qty:
                            #     purchase_id[(line.plan_date,line.partner_id.id)].append((key_new[0], key_new[1]+line.qty_jh,key_new[2],key_new[3],key_new[4]))
                            # else:
                            purchase_id[(line.plan_date,line.partner_id.id)].append((key_new[0], key_new[1]+line.qty,key_new[2],key_new[3],key_new[4]))
                            break
                    if not log:
                        # if line.qty_jh > line.qty:
                        #     purchase_id[(line.plan_date,line.partner_id.id)].append((line.product_id.id ,line.qty_jh, line.price_unit,line.name,line.uom_id.id))
                        # else:
                        #     purchase_id[(line.plan_date,line.partner_id.id)].append((line.product_id.id ,line.qty, line.price_unit,line.name,line.uom_id.id))
                        purchase_id[(line.plan_date,line.partner_id.id)].append((line.product_id.id ,line.qty_jh, line.price_unit,line.name,line.uom_id.id,line.product_manager.id))

                else:
                    # if line.qty_jh > line.qty:
                    #     purchase_id[(line.plan_date,line.partner_id.id)] = [(line.product_id.id ,line.qty_jh, line.price_unit,line.name,line.uom_id.id)]
                    # else:
                    #     purchase_id[(line.plan_date,line.partner_id.id)] = [(line.product_id.id ,line.qty, line.price_unit,line.name,line.uom_id.id)]

                    purchase_id[(line.plan_date,line.partner_id.id)] = [(line.product_id.id ,line.qty_jh, line.price_unit,line.name,line.uom_id.id,line.product_manager.id)]
            notes = ''
            # 创建采购单
            for key_line,value_line in purchase_id.items():
                # picking_type_ids = self.pool.get('stock.picking.type').search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', obj.company_id.id)])
                # if not picking_type_ids:
                #     picking_type_ids = self.pool.get('stock.picking.type').search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', False)])
                picking_type_id = obj.location_name.in_type_id
                res_id = purchase_obj.create(cr, uid, {'pricelist_id':partner_obj.browse(cr, uid, key_line[1]).property_product_pricelist_purchase.id,'plan_id':obj.id,'partner_id':key_line[1],'location_name':obj.location_name.id,
                                              'date_order':obj.create_date_new,'company_id':obj.company_id.id,'picking_type_id':picking_type_id.id,'notes':obj.notes_new,
                                              'location_id':picking_type_id.default_location_dest_id.id,'minimum_planned_date':obj.minimum_planned_date,'deal_date':key_line[0],
                                              })
                notes = notes + purchase_obj.browse(cr, uid, res_id).name + ';'
                # 创建采购订单明细
                for line_va in value_line:
                    purchase_line_obj.create(cr, uid, {'name':line_va[3],'order_id':res_id,'product_id':line_va[0],'date_planned':key_line[0],
                                                       'company_id':obj.company_id.id,'product_qty':line_va[1],'product_uom':line_va[4],
                                                       'price_unit':line_va[2],'product_manager':line_va[5]})
        return self.write(cr, uid, ids, {'state':'done','notes':notes})


class qdodoo_purchase_order_tfs(models.Model):
    _inherit = 'purchase.order'

    plan_id = fields.Many2one('qdodoo.plan.purchase.order',u'计划单')

class qdodoo_plan_purchase_order_line(models.Model):
    _name = 'qdodoo.plan.purchase.order.line'

    order_id = fields.Many2one('qdodoo.plan.purchase.order',u'计划转采购单')
    product_id = fields.Many2one('product.product',u'产品',required=True)
    plan_date_jh = fields.Date(u'到货日期(计划)',required=True)
    plan_date = fields.Date(u'到货日期(采购)')
    name = fields.Char(u'备注')
    price_unit = fields.Float(u'单价')
    qty_jh = fields.Float(u'数量(计划)',required=True)
    qty = fields.Float(u'数量(采购)')
    uom_id = fields.Many2one('product.uom',u'单位')
    partner_id = fields.Many2one('res.partner',u'供应商')
    state = fields.Selection([('draft',u'草稿'),('sent',u'待确认'),('apply',u'待审批'),('confirmed',u'转换采购单'),('done',u'完成')],u'状态', default='draft')
    colors = fields.Char(string=u'颜色', compute='_get_colors')
    is_cancel = fields.Boolean(u'需要回退', default=False)
    difference_num = fields.Float(u'计划和采购差异数量',compute='_get_difference_num')
    is_split = fields.Boolean(u'已拆分过')
    product_manager = fields.Many2one('res.users',u'产品经理')

    def _get_difference_num(self):
        for ids in self:
            ids.difference_num = ids.qty_jh - ids.qty

    # 获取颜色
    def _get_colors(self):
        for ids in self:
            if ids.plan_date_jh != ids.plan_date or ids.qty_jh != ids.qty:
                ids.colors = 'red'

    # 带出默认值
    def create(self, cr, uid, vals, context=None):
        print vals
        if not vals.get('plan_date') and vals.get('plan_date_jh'):
            vals['plan_date'] = vals.get('plan_date_jh')
        if not vals.get('qty') and vals.get('qty_jh'):
            vals['qty'] = vals.get('qty_jh')
        return super(qdodoo_plan_purchase_order_line, self).create(cr, uid, vals, context=context)

    #比较采购数量跟计划数量
    def onchange_qty(self, cr, uid, ids, qty_jh, qty, context=None):
        res={}

        if qty> qty_jh and qty_jh != 0:
            warning_msgs = "采购数量%d大于计划数量%d,请修正！" % (qty, qty_jh)
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
            res.update({'warning': warning})
        return res

    # 根据产品和供应商修改产品价格
    def onchange_product_id(self, cr, uid, ids, product_id, partner_id, qty, uom_id, company_id, context=None):
        product_pricelist = self.pool.get('product.pricelist')
        partner_obj = self.pool.get('res.partner')
        users_obj = self.pool.get('res.users')
        product_obj = self.pool.get('product.product')
        if ids:
            obj = self.browse(cr, uid, ids[0])
        res = {}
        res['value'] = {}
        date_order = datetime.now()
        if product_id:
            # 查询一个公司信息正确的用户
            # 查询有销售经理权限的id
            sql = """ select uid from res_groups_users_rel where gid = 10"""
            cr.execute(sql)
            uid_ids = [r[0] for r in cr.fetchall()]
            users_ids = users_obj.search(cr, uid, [('company_id','=',company_id),('id','in',uid_ids)])
            if not users_ids:
                raise osv.except_osv(_(u'错误'), _(u'对应公司缺少销售经理！'))
            product_obj = self.pool.get('product.product').browse(cr, users_ids[0], product_id, context=context)
            # 获取产品对应的供应商和送货周期\数量
            purchase_dict = {}
            purchase_num_dict = {}
            #唯一供应商默认填充到明细
            if len(product_obj.seller_ids) == 1:
                # 根据价格表有效期判断是否填充供应商
                date_end = datetime.strptime(product_obj.seller_ids.name.property_product_pricelist_purchase.version_id.date_end,'%Y-%m-%d')
                if  date_end > datetime.today():
                    res['value']['partner_id'] = product_obj.seller_ids.name.id
            #填充产品经理
            if product_obj.product_manager_tfs:
                res['value']['product_manager'] = product_obj.product_manager_tfs.id
            for line in product_obj.seller_ids:
                purchase_dict[line.name.id] = line.delay
                purchase_num_dict[line.name.id] = line.min_qty
            if partner_id:
                pricelist_id = partner_obj.browse(cr, users_ids[0], partner_id).property_product_pricelist_purchase.id
                date_order_str = date_order.strftime(DEFAULT_SERVER_DATE_FORMAT)
                price = product_pricelist.price_get(cr, users_ids[0], [pricelist_id],
                        product_id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
                res['value']['price_unit'] = price
                res['value']['plan_date'] = datetime.now().date() + timedelta(days=purchase_dict.get(partner_id,0))
                res['value']['qty'] = purchase_num_dict.get(partner_id, qty)
            else:
                res['value']['price_unit'] = 0.0
            res['value']['name'] = product_obj.product_tmpl_id.name
            res['value']['uom_id'] = product_obj.uom_id.id
            return res
        else:
            return {}

    # 拆单
    @api.multi
    def split_quantities(self):
        self.write({'is_split':True})
        self.copy({'qty':self.difference_num,'qty_jh':self.difference_num,'state':'sent'})
        view_ref = self.env['ir.model.data'].get_object_reference('qdodoo_plan_purchase_order', 'view_form_qdodoo_plan_purchase_order')
        view_id = view_ref and view_ref[1] or False,
        view_ref_tree = self.env['ir.model.data'].get_object_reference('qdodoo_plan_purchase_order', 'view_tree_qdodoo_plan_purchase_order')
        view_id_tree = view_ref_tree and view_ref_tree[1] or False,
        return {
            'type': 'ir.actions.act_window',
            'name': _('计划转采购'),
            'res_model': 'qdodoo.plan.purchase.order',
            'res_id': self.order_id.id,
            'view_type': 'form',
            'view_mode': 'form,tree',
            'views': [(view_id,'form'),(view_id_tree,'tree')],
            'view_id': view_id,
        }

class qdodoo_res_partner_inherit(models.Model):

    _inherit = 'res.partner'

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if args is None:
            args = []
        if context is None:
            context={}
        if context.get('qdodoo_log'):
            supplierinfo_obj = self.pool.get('product.supplierinfo')
            product_obj = self.pool.get('product.product')

            supplierinfo_ids = supplierinfo_obj.search(cr, uid, [('product_tmpl_id','=',product_obj.browse(cr, uid, context.get('product_id')).product_tmpl_id.id)])
            partner_list = []
            for supplierinfo_id in supplierinfo_obj.browse(cr, uid, supplierinfo_ids):
                pricelist = supplierinfo_id.name.property_product_pricelist_purchase.version_id
                if datetime.strptime(pricelist.date_end,'%Y-%m-%d') < datetime.today():
                    continue
                partner_list.append(supplierinfo_id.name.id)
            args.append(('id','in',partner_list))
        return super(qdodoo_res_partner_inherit, self).name_search(cr, uid, name, args=args, operator=operator, context=context, limit=limit)

class qdodoo_product_template(models.Model):
    """
        产品模板中增加产品经理
    """
    _inherit = 'product.template'

    product_manager_tfs = fields.Many2one('res.users',u'产品经理')

class purchase_order_line(models.Model):
    """
    采购订单明细增加产品经理字段
    """
    _inherit = 'purchase.order.line'

    product_manager = fields.Many2one('res.users', u'产品经理')