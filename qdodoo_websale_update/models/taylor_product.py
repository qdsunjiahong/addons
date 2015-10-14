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

    def  synchronous_field(self,cr ,uid, ids, context):
        """
        同步字段
        得到相对应的产品价格表
        把数值写入到关联对象之中
        """
        pricelist_prolate_obj=self.pool.get('pricelist.prolate.relation')
        price_lis_item=self.pool.get('product.pricelist.item')
        pricr_list_version=self.pool.get("product.pricelist.version")
        product_obj=self.pool.get('product.product')
        pric_var_now=""

        #遍历本地关联对象
        pricelist_prolate_list=pricelist_prolate_obj.search(cr ,uid ,[('ref_product_template','=',ids)],context=context)
        product_list=product_obj.search(cr ,uid  ,[('product_tmpl_id','=',ids)])
        for prolate_obj in pricelist_prolate_obj.browse(cr ,uid ,pricelist_prolate_list,context=context):

            #遍历价格表版本
            for pric_ver in pricr_list_version.browse(cr, uid ,pricr_list_version.search(cr ,uid ,[('pricelist_id','=',prolate_obj.ref_product_pricelist.id)],context=context),context=context):
                if not pric_ver.date_start and not pric_ver.date_end:
                    pric_var_now = pric_ver.id
                    break
                elif fields.datetime.now() < pric_ver.date_end and fields.datetime.now() > pric_ver.date_end:
                    pric_var_now = pric_ver.id
                    break
            #r如果存在价格版本
            if pric_var_now:
                #搜索出相对应的价格表列表
                # price_lis_item_id=price_lis_item.search(cr,uid,[('price_version_id','=',pric_var_now),('product_tmpl_id','=',prolate_obj.ref_product_template.id)],order="sequence desc",limit=1)
                # print 'price_lis_item_id is ', price_lis_item_id
                price_lis_item_obj = price_lis_item.browse(cr,uid ,price_lis_item.search(cr,uid,[('price_version_id','=',pric_var_now),('product_tmpl_id','=',product_list)],order="sequence desc",limit=1))
                if price_lis_item_obj:
                    result=prolate_obj.ref_product_template.list_price*(1+price_lis_item_obj.price_discount)+price_lis_item_obj.price_surcharge
                    pricelist_prolate_obj.write(cr,uid,prolate_obj.id,{'comparison':result,'success':True,'price_version_item_id':price_lis_item_obj.id})





    def  add_synchronous_field(self,cr ,uid, ids, context):
        """
        同步开始
        判断同步的值和当前的值是否一致 不一致 那么开始
        1.首先查找相应价格表
        2.搜索价格表关联的产品 通过产品搜索出相应的价格表列表
        3.得到同样的产品根据sequce来排序 取得第一个值 然后的到相应的值
        4.将我们目前的值进行保存
        """
        #得到相关对象
        pricelist_prolate_obj=self.pool.get('pricelist.prolate.relation')
        price_lis_item=self.pool.get('product.pricelist.item')
        pricr_list_version=self.pool.get("product.pricelist.version")
        product_obj=self.pool.get('product.product')

        #遍历本地关联对象
        pricelist_prolate_list=pricelist_prolate_obj.search(cr ,uid ,[('ref_product_template','=',ids)],context=context)
        for prolate_obj in pricelist_prolate_obj.browse(cr ,uid ,pricelist_prolate_list,context=context):
            #如果已经创建了
            if prolate_obj.success:
                #如果两个取值不一样
                if not prolate_obj.to_toal == prolate_obj.comparison:
                    #查找对应价格列 修改价格列中的数值
                    value={
                    'price_discount':prolate_obj.proportion,
                    'price_surcharge':prolate_obj.fixed,
                    }
                    price_lis_item.write(cr ,uid, prolate_obj.price_version_item_id,value,context=context)
        self.synchronous_field(cr,uid,ids,context)


    def add_price_list(self ,cr ,uid, ids, context):
        #print 'add_price_list args uid',uid,'ids ', ids ,'context',context

        pricelist_prolate_obj=self.pool.get('pricelist.prolate.relation')
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
                raise Warning(_('没有这个价格表，请重新选择'))

            #遍历相应的产品
            for product_id in product_obj.search(cr ,uid ,[('product_tmpl_id','=',prolate_obj.ref_product_template.id)],context=context):
                if not prolate_obj.success:
                    values={
                    'price_version_id':pric_var_now,
                    'product_tmpl_id':prolate_obj.ref_product_template.id,
                    'price_discount':prolate_obj.proportion,
                    'price_surcharge':prolate_obj.fixed,
                    'base':1,
                     }
                    values['product_id']=product_id
                    #创建相应的价格表明细
                    price_lis_it_id=price_lis_item.create(cr,uid,values,context=context)
                    if price_lis_it_id:
                        pricelist_prolate_obj.write(cr ,uid ,prolate_obj.id,{'success':True,'price_version_item_id':price_lis_it_id},context=context)
                else:
                    values={
                    'price_version_id':pric_var_now,
                    'product_tmpl_id':prolate_obj.ref_product_template.id,
                    'price_discount':prolate_obj.proportion,
                    'price_surcharge':prolate_obj.fixed,
                    'base':1,
                     }
                    values['product_id']=product_id
                    price_lis_item.write(cr,uid,prolate_obj.price_version_item_id,values,context=context)



class pricelist_prolate_relation(models.Model):
    _name = "pricelist.prolate.relation"

    # 计算字段
    proportion = fields.Float('折扣')
    # public_price = fields.Float(compute="compute_public_price", string='公共价格')
    fixed = fields.Float('固定值')
    to_toal = fields.Float(string='单价', required=True, compute="compute_toal")
    success=fields.Boolean(string='是否创建',readonly=True)
    comparison=fields.Float(string="对比值",readonly=True)

    company=fields.Many2one('res.company',string='公司')
    price_version_item_id=fields.Integer(string='对应的价格表版本行')
    # 关联字段
    ref_product_pricelist = fields.Many2one('product.pricelist', '价格表',domain=['&',('type','=','sale'),('company_id','=',False)])
    ref_product_template = fields.Many2one('product.template', string='产品模版')




    def _get_company(self, cr  ,uid, ids ,context=None):
        user=self.pool.get('res.users')
        print 'user is ',user
        return  user.browse(cr,uid,uid).company_id.id

    _defaults =  {
        'company':_get_company,

    }
    def compute_toal(self):
        self.to_toal = (1 + self.proportion) * self.ref_product_template.list_price + self.fixed


    # def compute_public_price(self):
    #     pro_temp=self.env['product.template']
    #     self.public_price =  pro_temp.browse(self.ref_product_template).i


    #
    # @api.constrains('proportion')
    # def proportion_constrains(self):
    #     #print '99999999999999999999',self.proportion
    #     if self.proportion < 0 or self.proportion > 1:
    #         raise Warning(_('比例值在0-1之间'))



