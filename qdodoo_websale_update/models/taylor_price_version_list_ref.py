# -*- coding: utf-8 -*-

from openerp import models, fields, _, api
from openerp.exceptions import except_orm

class taylor_price_version_list(models.Model):
    """
        添加价格表版本与价格表关联
    """
    _name = "price.list.version"

    pricelist = fields.Many2one('product.pricelist', '价格表', required=True)
    perice_version = fields.Many2one('product.pricelist.version', '价格表版本')


class taylor_pricce_version(models.Model):
    """
        添加一个价格表版本与价格表关联字段
    """

    _inherit = "product.pricelist.version"

    price_list_ref = fields.One2many('price.list.version', 'perice_version', '相关价格表')

    def add_price_list(self, cr, uid, ids, context=None):
        print 'cr', cr, 'uid ', uid, 'ids', ids, 'context', context
        list_version = self.pool.get('price.list.version')
        product_pricelist = self.pool.get('product.pricelist')
        pricr_list_version = self.pool.get("product.pricelist.version")

        this = self.browse(cr, uid, ids[0], context=context)
        print 'this is ', this
        # 查找相对用的版本关联表
        list_version_list = list_version.search(cr, uid, [('perice_version', 'in', ids)], context=context)
        # 遍历出所有的价格表关联
        for list_version_obj in list_version.browse(cr, uid, list_version_list, context=context):
            print 'list_version_obj is ', list_version_obj
            # 查找相应的价格表
            # 价格表为list_version_obj.pricelist.id
            # 查找价格表是否存在这个 价格表版本id
            pricr_list_version_ids=pricr_list_version.search(cr, uid, [('pricelist_id','=',list_version_obj.pricelist.id)],context=context)
            #查询出版本
            vewssion_list=[]
            for i in pricr_list_version.browse(cr, uid, pricr_list_version_ids, context=context):
                if i.name not in vewssion_list:
                    vewssion_list.append(i.name)
            if this.name not in vewssion_list:
                version_id=self.copy(cr, uid, this.id,
                                   {'pricelist_id': list_version_obj.pricelist.id, 'price_list_ref': None,'active':True}, context=context)
                self.write(cr ,uid ,version_id ,{'active':True},context=context)
                print 'version_id is==' ,version_id


class taylor_pricce_list(models.Model):

    _inherit = "product.pricelist.item"

    multipl= fields.Float('倍数')

    _defaults = {
        'multipl':1,
    }

    @api.constrains('multipl')
    def _check_quantity_price(self):
        if self.multipl<0:
            raise except_orm(_('Warning!'),_('警告,倍数必须大于0！'))