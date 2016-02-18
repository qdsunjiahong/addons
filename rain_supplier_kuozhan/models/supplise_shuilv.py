#-*- coding:utf-8 -*-

from openerp import models,fields,_,api
from openerp.tools.sql import drop_view_if_exists

class rain_supplise_ex(models.Model):
    _name = 'supplise.ex'


    @api.one
    def name_get(self):
        name=(100*self.shuilv)/100
        return (self.id,str(name)+'%')
    @api.one
    def _get_display_name(self):
        result = self.name_get()
        if len(result):
            self.complete_name = result[0][1]

    name=fields.Char('公司名称',required=False)
    company_id = fields.Many2one('res.partner',u'公司名称',required=True)
    property_supplier_payment_term=fields.Many2one('account.payment.term',u'供应商支付条款')
    open_supp=fields.Selection([('yes','必选'),('no','不需要')],u'开票需求')
    complete_name = fields.Char('Display Name',compute="_get_display_name")
    shuilv=fields.Selection([('0','0%'),('3','3%'),('6','6%'),('11','11%'),('13','13%'),('17','17%')],u'税率')
    partner_id=fields.Many2one('res.partner',u'供应商名称')

class inherit_account_bottom(models.Model):
    _inherit='res.partner'

    show_supplise=fields.One2many('supplise.ex','partner_id',string="show_supplise")
    ref_new=fields.Char("编号",required=True)
    _sql_constraints = [
        ('ref_unique_only',
         'UNIQUE(ref_new)',
         '编号不能重复!'),
    ]

class qdodoo_supplier_infor(models.Model):
    _name = 'qdodoo.supplier.infor'

    supplier_id = fields.Many2one('res.partner',u'供应商名称')
    addres = fields.Char(u'地址')
    website = fields.Char(u'网址')
    phone = fields.Char(u'电话')
    mobile = fields.Char(u'手机')
    QQ = fields.Char('QQ')
    fax = fields.Char(u'传真')
    email = fields.Char(u'邮箱')
    title = fields.Many2one('res.partner.title',u'称谓')
    contact_people = fields.Char(u'联系人')
    acc_number = fields.Char(u'银行账号')
    bank_name = fields.Char(u'银行名称')
    company_id = fields.Many2one('res.partner',u'公司名称')
    property_supplier_payment_term = fields.Many2one('account.payment.term',u'供应商付款方式')
    open_supp=fields.Selection([('yes','必选'),('no','不需要')],u'开票需求')
    shuilv=fields.Selection([('0','0%'),('3','3%'),('6','6%'),('11','11%'),('13','13%'),('17','17%')],u'税率')


class qdodoo_supplier_infor_search(models.Model):
    _name = 'qdodoo.supplier.infor.search'

    def btn_search(self, cr, uid, ids, context=None):
        # 创建数据
        # 查询供应商
        all_ids = self.search(cr, uid, [])
        self.unlink(cr, uid, all_ids)
        partner_obj = self.pool.get('res.partner')
        supplier_obj = self.pool.get('qdodoo.supplier.infor')
        supplier_ids = supplier_obj.search(cr, uid, [])
        supplier_obj.unlink(cr, uid, supplier_ids)
        supplier = partner_obj.search(cr, uid, [('supplier','=',True)])
        move_lst = []
        for line in partner_obj.browse(cr, uid, supplier):
            if line.bank_ids:
                for line1 in line.bank_ids:
                    if line.show_supplise:
                        for line3 in line.show_supplise:
                            res_id = supplier_obj.create(cr, uid, {'supplier_id':line.id,'addres':line.street,'website':line.website,'phone':line.phone,
                                                          'mobile':line.mobile,'QQ':line.QQ,'fax':line.fax,'email':line.email,
                                                          'title':line.title.id if line.title else '',
                                                                   # 'contact_people':line.contact_people,
                                                          'acc_number':line1.acc_number,'bank_name':line1.bank_name,'company_id':line3.company_id.id,
                                                          'property_supplier_payment_term':line3.property_supplier_payment_term.id,'open_supp':line3.open_supp,
                                                          'shuilv':line3.shuilv})
                            move_lst.append(res_id)
                    else:
                        res_id = supplier_obj.create(cr, uid, {'supplier_id':line.id,'addres':line.street,'website':line.website,'phone':line.phone,
                                                          'mobile':line.mobile,'QQ':line.QQ,'fax':line.fax,'email':line.email,
                                                          'title':line.title.id if line.title else '',
                                                               # 'contact_people':line.contact_people,
                                                          'acc_number':line1.acc_number,'bank_name':line1.bank_name})
                        move_lst.append(res_id)
            else:
                if line.show_supplise:
                    for line2 in line.show_supplise:
                        res_id = supplier_obj.create(cr, uid, {'supplier_id':line.id,'addres':line.street,'website':line.website,'phone':line.phone,
                                                          'mobile':line.mobile,'QQ':line.QQ,'fax':line.fax,'email':line.email,
                                                          'title':line.title.id if line.title else '',
                                                               # 'contact_people':line.contact_people,
                                                          'company_id':line2.company_id.id,
                                                          'property_supplier_payment_term':line2.property_supplier_payment_term.id,'open_supp':line2.open_supp,
                                                          'shuilv':line2.shuilv})
                        move_lst.append(res_id)
                else:
                    res_id = supplier_obj.create(cr, uid, {'supplier_id':line.id,'addres':line.street,'website':line.website,'phone':line.phone,
                                                  'mobile':line.mobile,'QQ':line.QQ,'fax':line.fax,'email':line.email,
                                                  'title':line.title.id if line.title else '',
                                                           # 'contact_people':line.contact_people
                                                           })
                    move_lst.append(res_id)
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'rain_supplier_kuozhan', 'tree_supplier_information')
        view_id = result and result[1] or False
        return {
              'name': ('发票'),
              'view_type': 'form',
              "view_mode": 'tree',
              'res_model': 'qdodoo.supplier.infor',
              'type': 'ir.actions.act_window',
              'domain': [('id','in',move_lst)],
              'view_id': [view_id],
              }
