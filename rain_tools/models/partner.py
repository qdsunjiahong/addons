# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import xlrd, base64
from openerp.tools.translate import _
import sys
import types
reload(sys)
sys.setdefaultencoding('utf8')

class partner_import(osv.osv_memory):
    _name = 'rain.partner.import'

    _columns = {
        'db_datas': fields.binary('Database Data'),
    }

    def action_upload(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        value = self.browse(cr, uid, ids[0]).db_datas
        wb = xlrd.open_workbook(file_contents=base64.decodestring(value))
        sh = wb.sheet_by_index(0)
        nrows = sh.nrows

        partner_pool = self.pool.get("res.partner")
        country_pool = self.pool.get("res.country")
        state_pool = self.pool.get("res.country.state")
        city_pool = self.pool.get('hm.city')
        district_pool = self.pool.get('hm.district')
        account_pool = self.pool.get('account.payment.term')
        bank_pool = self.pool.get('res.partner.bank')


        for rownum in range(2, nrows):
            args = {}
            bank_val = {}

            #是否是公司［Y/N] 0 is_company
            # sh_is_company = sh.cell(rownum, 0).value.strip()
            # if  sh_is_company != "":
            #     if sh_is_company == "Y":
            #         args['is_company'] = True
            #     else:
            #         args['is_company'] = False
            # else:
            #     raise osv.except_osv("导入出错:", _(u'是否为公司:不能为空，请添加;行号:%d' % (rownum + 1)))

            #集团内部部门[Y/N] 1
            # sh_is_internal = sh.cell(rownum, 1).value.strip()
            # if  sh_is_internal != "":
            #     if sh_is_internal == "Y":
            #         args['is_internal'] = True
            #     else:
            #         args['is_internal'] = False
            # else:
            #     raise osv.except_osv("导入出错:", _(u'是否公司内部:不能为空， 请添加;行号:%d' % (rownum + 1)))

            #名称 2
            sh_name = sh.cell(rownum, 2).value.strip()
            if  sh_name != "":
               args['name'] = sh_name
            else:
                raise osv.except_osv("导入出错:", _(u'名称:不能为空， 请添加;行号:%d' % (rownum + 1)))

            #地址[国家／省／市／区／街道] 3
            # sh_address = sh.cell(rownum, 3).value.strip()
            # if sh_address != '':
            #     address_array = sh_address.split(',')
            #     #国家0
            #     add_country = address_array[0]
            #     print add_country
            #     country_ids = country_pool.search(cr, uid, [('name','=',add_country)])
            #     if len(country_ids) > 0:
            #         args['country_id'] = country_ids[0]
            #     else:
            #         raise osv.except_osv("导入出错:", _(u'国家不存在， 请添加该国家;行号:%d' % (rownum + 1)))
            #
            #     #省1
            #     add_state = address_array[1]
            #     state_ids = state_pool.search(cr, uid, [('name','=',add_state),('country_id','=',country_ids[0])])
            #     if len(state_ids) > 0:
            #         args['state_id'] = state_ids[0]
            #     else:
            #         raise osv.except_osv("导入出错:", _(u'省不存在， 请添加该省;行号:%d' % (rownum + 1)))
            #
            #     #市2
            #     add_city = address_array[2]
            #     city_ids = city_pool.search(cr, uid, [('name','=',add_city),('state','=',state_ids[0])])
            #     if len(city_ids) > 0:
            #         args['city'] = city_ids[0]
            #     else:
            #         raise osv.except_osv("导入出错:", _(u'城市不存在， 请添加该城市;行号:%d' % (rownum + 1)))
            #
            #     #区3
            #     add_district = address_array[3]
            #     district_ids = district_pool.search(cr, uid, [('name','=',add_district),('city','=',city_ids[0])])
            #     if len(district_ids) > 0:
            #         args['district'] = district_ids[0]
            #     else:
            #         raise osv.except_osv("导入出错:", _(u'区不存在， 请添加该区;行号:%d' % (rownum + 1)))
            #
            #     #街道4
            #     if len(address_array) > 4:
            #         args['street'] = address_array[4]
            #         print address_array


            #电话 4


            #手机 5
            sh_mobile = sh.cell(rownum, 5).value
            if type(sh_mobile) == type(1) or type(sh_mobile) == type(1.0):
                #是数字
                args['mobile'] = '%d'%int(sh_mobile)
            elif  sh_mobile != "":
               args['mobile'] = sh_mobile


            #电子邮件 6 email
            sh_email = sh.cell(rownum, 6).value
            if sh_email != '':
                args['email'] = sh_email

            #ＱＱ号 7
            sh_qq = sh.cell(rownum, 7).value
            if type(sh_qq) == type(1) or type(sh_qq) == type(1.0):
                #是数字
                args['QQ'] = '%d'%int(sh_qq)
            elif  sh_name != "":
               args['QQ'] = sh_qq

            #内部备注 8 comment
            sh_comment = sh.cell(rownum, 8).value
            if sh_comment != '':
                args['comment'] = sh_comment

            #编号 9 ref
            sh_ref = sh.cell(rownum, 9).value
            if type(sh_ref) == type(1) or type(sh_ref) == type(1.0):
                #是数字
                args['ref'] = '%d'%int(sh_ref)
            elif  sh_ref != "":
               args['ref'] = sh_ref

            #合同开始日期 10
            # sh_date = sh.cell(rownum, 10).value
            # if sh_comment != '':
            #     args['date'] = sh_date

            #合同结束日期 11
            # sh_contract_end_date = sh.cell(rownum, 11).value
            # if sh_contract_end_date != '':
            #     args['contract_end_date'] = sh_contract_end_date

            #联系人 12
            sh_icontact = sh.cell(rownum, 12).value
            if sh_icontact != '':
                args['icontact'] = sh_icontact

            #付款方式 13 property_supplier_payment_term
            sh_payment_term = sh.cell(rownum, 13).value
            if sh_payment_term != "":
                print sh_payment_term
                print len(sh_payment_term)
                payment_ids = account_pool.search(cr, uid,[('name','=',sh_payment_term)] )
                if len(payment_ids) > 0:
                    args['property_supplier_payment_term'] = payment_ids[0]
                else:
                    raise osv.except_osv("导入出错:", _(u'付款方式不存在， (会计－> 其他－>付款方式)请添加该付款方式;行号:%d' % (rownum + 1)))

            sh_acc_number = sh.cell(rownum, 14).value
            sh_bank_name = sh.cell(rownum, 15).value
            sh_owner_name = sh.cell(rownum, 16).value
            if sh_acc_number != "" and sh_bank_name != "":
                bank_val = {'state': 'bank',
                                'acc_number': sh_acc_number,
                                'bank_name': sh_bank_name,

                                }
                if sh_owner_name != "":
                    bank_val['owner_name'] = sh_owner_name
                else:
                    bank_val['owner_name'] = sh_name
            else:
                raise osv.except_osv("导入出错:", _(u'银行帐户不完整，请修正;行号:%d' % (rownum + 1)))


            args['supplier'] = True
            args['customer'] = False

            if bank_val:
                args['bank_ids'] = [[0, False, bank_val]]
            partner_pool.create(cr, uid, args)


partner_import()