# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class taylor_template(models.Model):
    """
        在产品中添加相关价格表关联
        这样可以有效减少业务人员的操作量
    """

    _inherit = 'product.template'


    # 关联字段

    ref_pricelist_prolate = fields.One2many('pricelist.prolate.relation', 'ref_product_template', string='关联的价格表')


    def add_price_list(self ,cr ,uid, ids, context):
        #print 'add_price_list args uid',uid,'ids ', ids ,'context',context

        pricelist_prolate_obj=self.pool.get('pricelist.prolate.relation')
        price_list_obj=self.pool.get('product.pricelist')
        price_lis_item=self.pool.get('product.pricelist.item')
        pricr_list_version=self.pool.get("product.pricelist.version")
        product_obj=self.pool.get('product.product')
        #遍历所要添加的产品价格表
        pric_var_now=""
        pricelist_prolate_list=pricelist_prolate_obj.search(cr ,uid ,[('ref_product_template','=',ids)],context=context)
        for prolate_obj in pricelist_prolate_obj.browse(cr ,uid ,pricelist_prolate_list,context=context):
            #print 'prolate_obj_id',prolate_obj
            #print 'prolate_obj_id.ref_product_pricelist :',prolate_obj.ref_product_pricelist.id

            #遍历价格表版本
            for pric_ver in pricr_list_version.browse(cr, uid ,pricr_list_version.search(cr ,uid ,[('pricelist_id','=',prolate_obj.ref_product_pricelist.id)],context=context),context=context):
                if  not pric_ver.date_start and  not  pric_ver.date_end:
                    pric_var_now=pric_ver.id
                    break
                elif fields.datetime.now()<pric_ver.date_end and fields.datetime.now()>pric_ver.date_end:
                    pric_var_now=pric_ver.id
                    break
            #print 'pric_var_now is ',pric_var_now
            if not pric_var_now:
                raise Warning(_('比例值在0-1之间'))

            #遍历相应的产品
            for product_id in product_obj.search(cr ,uid ,[('product_tmpl_id','=',prolate_obj.ref_product_template.id)],context=context):
                values={
                    'price_version_id':pric_var_now,
                    'product_tmpl_id':prolate_obj.ref_product_template.id,
                    'price_discount':prolate_obj.proportion,
                    'price_surcharge':prolate_obj.fixed,
                    'base':1,
                }
                values['product_id']=product_id
                if not prolate_obj.success:
                    #创建相应的价格表明细
                    price_lis_it_id=price_lis_item.create(cr,uid,values,context=context)
                    if price_lis_it_id:
                        pricelist_prolate_obj.write(cr ,uid ,prolate_obj.id,{'success':True},context=context)




class pricelist_prolate_relation(models.Model):
    _name = "pricelist.prolate.relation"

    # 计算字段
    proportion = fields.Float('比例')
    # public_price = fields.Float(compute="compute_public_price", string='公共价格')
    fixed = fields.Float('固定值')
    to_toal = fields.Float(string='单价', required=True, compute="compute_toal")
    success=fields.Boolean(string='是否创建',readonly=True)

    # 关联字段
    ref_product_pricelist = fields.Many2one('product.pricelist', '价格表',domain=[('type','=','sale')])
    ref_product_template = fields.Many2one('product.template', string='产品模版')


    def compute_toal(self):
        self.to_toal = (1 + self.proportion) * self.ref_product_template.list_price + self.fixed


    # def compute_public_price(self):
    #     pro_temp=self.env['product.template']
    #     self.public_price =  pro_temp.browse(self.ref_product_template).i


    #
    @api.constrains('proportion')
    def proportion_constrains(self):
        #print '99999999999999999999',self.proportion
        if self.proportion < 0 or self.proportion > 1:
            raise Warning(_('比例值在0-1之间'))

