# -*- coding: utf-8 -*-

import hashlib
import os
import re
from openerp import tools
from openerp.tools.translate import _
import datetime

from openerp.osv import fields, osv
import xlrd,base64

class hr_department(osv.osv):
    _name = "hr.department"
    _inherit = "hr.department"

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

hr_department()

class hr_employee_import(osv.osv):
    _name = "hr.employee.import"

    def id_by_complete_name(self, cr, uid, complete_name,context=None):
        """
            根据完整名字获取 id
        :param cr:
        :param uid:
        :param complete_name:
        :param context:
        :return:
        """

        #获取所有部门
        department_ids = self.pool.get("hr.department").search(cr, uid,[])
        if len(department_ids) > 0:
            department_objs = self.pool.get("hr.department").browse(cr, uid, department_ids)
            for department_obj in department_objs:
                if department_obj.complete_name == complete_name:
                    print department_obj.complete_name
                    return department_obj.id

        return False

    def action_upload(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        value = self.browse(cr, uid, ids[0]).db_datas
        wb = xlrd.open_workbook(file_contents=base64.decodestring(value))

        sh = wb.sheet_by_index(0)
        nrows = sh.nrows
        for rownum in range(3, nrows):
            employee = self.pool.get("hr.employee")
            args = {}

            # sh_default_code = sh.cell(rownum,1).value
            # print sh_default_code
            # if type(sh_default_code) == type(1) or type(sh_default_code) == type(1.0):
            #     #是数字
            #     args['default_code'] = '%d'%int(sh_default_code)
            # elif  sh_default_code != "":
            #    args['default_code'] = sh_default_code


            #0 员工编号


            # sh_default_code = sh.cell(rownum,1).value
            # print sh_default_code
            # if type(sh_default_code) == type(1) or type(sh_default_code) == type(1.0):
            #     #是数字
            #     args['default_code'] = '%d'%int(sh_default_code)
            # elif  sh_default_code != "":
            #    args['default_code'] = sh_default_code
            sh_e_no = sh.cell(rownum, 0).value
            if sh_e_no != "":
                args['e_no'] = sh_e_no


            #1 2 英文名
            sh_e_name = sh.cell(rownum, 2).value
            if sh_e_name != "":
                args['e_name'] = sh_e_name

            sh_name = sh.cell(rownum, 1).value
            if sh_name != "":
                args["name"] = sh_name


            #3 性别（男, 女）
            # sh_gender = sh.cell(rownum, 3).value
            # if sh_gender == '男':
            #     args['gender'] = 'male'
            # else:
            #     args['gender'] = 'female'



            #4 岗位（职位 job_id)
            sh_job_id_name = sh.cell(rownum, 4).value
            job_ids = self.pool.get('hr.job').search(cr, uid, [('name', '=', sh_job_id_name)], context = context)
            if len(job_ids) == 0:
                job_id = self.pool.get('hr.job').create(cr, uid,{'name': sh_job_id_name},context=context)
                args['job_id'] = job_id
            else:
                args['job_id'] = job_ids[0]
            #
            #5 职级(分类）
            sh_category = sh.cell(rownum,5).value
            if sh_category != "":
                category_names = sh_category.split(",")
                category_ids = self.pool.get("hr.employee.category").search(cr, uid,[('name', 'in', category_names)],context=context)
                args["category_ids"] = [(6,0,category_ids)]

            #6 是否部门负责人
            sh_manager = sh.cell(rownum,6).value
            if sh_manager == u'是':
                args['manager'] = True
            else:
                args['manager'] = False

            department_name = ''
            ####部门 一级部门 / 二级部门 / 三级部门 / department_id
            #7 一级部门
            sh_department1 = sh.cell(rownum,7).value
            if sh_department1 != '':
                department_name = sh_department1
            #8 二级部门
            sh_department2 = sh.cell(rownum,8).value
            if sh_department2 != '':
                department_name = department_name + ' / ' + sh_department2
            #9 三级部门
            sh_department3 = sh.cell(rownum,9).value
            if sh_department3 != '':
                department_name = department_name + ' / ' + sh_department3
            #10 四级部门
            sh_department4 = sh.cell(rownum,10).value
            if sh_department4 != '':
                department_name = department_name + ' / ' + sh_department4

            #department_obj = self.pool.get('hr.department').browse(cr,uid,0)
            deparment_id = self.id_by_complete_name(cr,uid,department_name)
            if deparment_id:
                args['department_id'] = deparment_id





            #11 工作地点 work_location
            sh_work_location = sh.cell(rownum, 11).value
            args['work_location'] = sh_work_location

            #12 办公手机 mobile_phone
            sh_mobile_phone = sh.cell(rownum, 12).value
            args['mobile_phone'] = sh_mobile_phone

            #13 外部电子邮箱 work_email
            sh_work_email = sh.cell(rownum, 13).value
            args['work_email'] = sh_work_email

            #14 在职状态

            #15 国籍 country_id
            # sh_country_id_name = sh.cell(rownum, 15).value
            # country_ids = self.pool.get('res.country').search(cr, uid, [('name', 'in', sh_country_id_name)], context = context)
            # if len(country_ids) == 0:
            #     raise  osv.except_osv("导入出错:", _(u'导入的国籍错误:' + sh_country_id_name + u';行号:%d' % (rownum + 1)))
            # args['country_id'] = country_ids[0]

            #16 紧急联系人1 e_emergency_contact
            sh_e_emergency_contact = sh.cell(rownum, 16).value
            args['e_emergency_contact'] = sh_e_emergency_contact

            #17 紧急联系人与本人关系

            #18 紧急联系方式1 e_emergency_relation
            sh_e_emergency_relation = sh.cell(rownum, 18).value
            args['e_emergency_relation'] = sh_e_emergency_relation

            #19 联系电话 e_emergency_phone
            sh_e_emergency_phone = sh.cell(rownum, 19).value
            args['e_emergency_phone'] = sh_e_emergency_phone


            #20 身份证号码 identification_id
            sh_identification_id = sh.cell(rownum, 20).value
            args['identification_id'] = sh_identification_id


            # #21 出生日期 （月/日/年） birthday
            # sh_birthday = sh.cell(rownum, 21).value
            # if sh_birthday != '':
            #     print sh_birthday
            #     raise osv.except_osv("导入出错:", rownum)
            #     args['birthday'] = datetime.datetime.strptime(sh_birthday, '%m/%d/%Y')

            #22 年龄

            #23 婚育
            sh_marital = sh.cell(rownum, 23).value
            marital = ''
            if sh_marital is u"单身":
                marital = "single"
            elif sh_marital is u"已婚":
                marital = "married"
            elif sh_marital is u"配偶已经去世":
                marital = "widower"
            elif sh_marital is u"离异":
                marital = "divorced"

            args["marital"] = marital

            #24 子女数
            sh_children = sh.cell(rownum, 24).value
            args["children"] = sh_children

            #25 户口性质 e_hukou_type
            sh_e_hukou_type = sh.cell(rownum, 25).value
            if sh_e_hukou_type == u'城镇':
                args['e_hukou_type'] = 'urban'
            elif sh_e_hukou_type == u'农村':
                args['e_hukou_type'] = 'rural'


            #26 户口类型 e_hukou_location
            sh_e_hukou_location = sh.cell(rownum, 26).value
            if sh_e_hukou_location == u'本地':
                args['e_hukou_location'] = 'urban'
            elif sh_e_hukou_location == u'外地':
                args['e_hukou_location'] = 'rural'


            #27 现地址 e_address
            sh_e_address = sh.cell(rownum, 27).value
            args['e_address'] = sh_e_address

            #28 户籍地址
            sh_e_hukou_address = sh.cell(rownum, 28).value
            args['e_hukou_address'] = sh_e_hukou_address

            #29 是否租房

            sh_e_rent = sh.cell(rownum,29).value
            if sh_e_rent == '是':
                args['e_rent'] = True
            else:
                args['e_rent'] = False


            # #30 入职日期（月/日/年） e_recruit_date
            # sh_e_recruit_date = sh.cell(rownum, 30).value
            # if sh_e_recruit_date != '':
            #     args['e_recruit_date'] = datetime.datetime.strptime(sh_e_recruit_date, '%m/%d/%Y')

            #31 定岗日期（月/日/年）

            #32 工龄

            #33 合同类型 e_contract_type
            sh_e_contract_type = sh.cell(rownum,33).value
            if sh_e_contract_type == u'固定期':
                args['e_contract_type'] = 'fix'

            #34 工时制 e_workhour_type
            sh_e_workhour_type = sh.cell(rownum,34).value
            if sh_e_workhour_type == u'固定':
                args['e_workhour_type'] = 'fix'
            elif sh_e_workhour_type == u'综合':
                args['e_workhour_type'] = 'all'

            #35 劳动关系类型（实习/正式） e_hire_type
            sh_e_hire_type = sh.cell(rownum, 35).value
            if sh_e_hire_type == u'试用':
                args['e_hire_type'] = 'probation'
            elif sh_e_hire_type == u'正式':
                args['e_hire_type'] = 'official'
            elif sh_e_hire_type == u'钟点工':
                args['e_hire_type'] = 'hour'
            elif sh_e_hire_type == u'返聘':
                args['e_hire_type'] = 'back'

            #36 签订合同次数
            # sh_e_contract_times = sh.cell(rownum, 36).value
            # args['e_contract_times'] =  sh_e_contract_times

            #37 合同起 （月/日/年） e_contract_start
            # sh_e_contract_start = sh.cell(rownum, 37).value
            # if sh_e_contract_start != '':
            #     args['e_contract_start'] = datetime.datetime.strptime(sh_e_contract_start, '%m/%d/%Y')

            # #38 试用期内 e_probation_lenth
            # sh_e_probation_lenth = sh.cell(rownum, 38).value
            # args['e_probation_lenth'] =  sh_e_probation_lenth

            #39 合同止 （月/日/年）
            # sh_e_contract_stop = sh.cell(rownum, 39).value
            # if sh_e_contract_stop != '':
            #     args['e_contract_stop'] = datetime.datetime.strptime(sh_e_contract_stop, '%m/%d/%Y')

            #40 社保缴纳时间 e_ss_date
            # sh_e_ss_date = sh.cell(rownum, 40).value
            # if sh_e_ss_date != '':
            #     args['e_ss_date'] = datetime.datetime.strptime(sh_e_ss_date, '%m/%d/%Y')

            #41 社保基数 e_ss_base
            # sh_e_ss_base = sh.cell(rownum, 41).value
            # args['e_ss_base'] =  sh_e_ss_base

            #42 意外险截止日期 e_accident_insurance_stop
            # sh_e_accident_insurance_stop = sh.cell(rownum, 42).value
            # if sh_e_accident_insurance_stop != '':
            #     args['e_accident_insurance_stop'] = datetime.datetime.strptime(sh_e_accident_insurance_stop, '%m/%d/%Y')


            # #43 社保编号 e_ss_no
            # sh_e_ss_no= sh.cell(rownum, 43).value
            # if sh_e_ss_no != "":
            #     args['e_ss_no'] =  sh_e_ss_no

            #44 公积金缴纳时间 e_provident_fund_date
            # sh_e_provident_fund_date = sh.cell(rownum, 44).value
            # if sh_e_provident_fund_date != '':
            #     args['e_provident_fund_date'] = datetime.datetime.strptime(sh_e_provident_fund_date, '%m/%d/%Y')

            #45 公积金基数 e_provident_fund_base
            # sh_e_provident_fund_base= sh.cell(rownum, 45).value
            # args['e_provident_fund_base'] =  sh_e_provident_fund_base

            #46 公积金编号 e_provident_fund_no
            sh_e_provident_fund_no= sh.cell(rownum, 46).value
            args['e_provident_fund_no'] =  sh_e_provident_fund_no
            #47 银行卡号
            # sh_e_provident_fund_base= sh.cell(rownum, 47).value
            # args['e_provident_fund_base'] =  sh_e_provident_fund_base

            #48 第一学历 e_education_backgroud
            sh_e_education_backgroud = sh.cell(rownum, 48).value
            args['e_education_backgroud'] =  sh_e_education_backgroud

            #49 专业 e_major
            sh_e_major = sh.cell(rownum, 49).value
            args['e_major'] =  sh_e_major

            #50 毕业院校 e_university
            sh_e_university = sh.cell(rownum, 50).value
            args['e_university'] =  sh_e_university

            #50 毕业时间 e_graduated_date
            # sh_e_graduated_date = sh.cell(rownum, 51).value
            # if sh_e_graduated_date != '':
            #     args['e_graduated_date'] = datetime.datetime.strptime(sh_e_graduated_date, '%m/%d/%Y')

            #51 最高学历 e_highest_education
            sh_e_highest_education = sh.cell(rownum, 52).value
            args['e_highest_education'] =  sh_e_highest_education

            #52 最高学历专业 e_highest_major
            sh_e_highest_major = sh.cell(rownum, 53).value
            args['e_highest_major'] =  sh_e_highest_major

            #53 资格证到期时间 e_certificated_date
            # sh_e_certificated_date = sh.cell(rownum, 54).value
            # if sh_e_certificated_date != '':
            #     args['e_certificated_date'] = datetime.datetime.strptime(sh_e_certificated_date, '%m/%d/%Y')

            #54 执业资格/技能证书 e_certification
            sh_e_certification = sh.cell(rownum, 55).value
            args['e_certification'] =  sh_e_certification

            #55 健康证到期时间

            #56 离职日期 e_dimission_date
            # sh_e_dimission_date = sh.cell(rownum, 57).value
            # if sh_e_dimission_date != '':
            #     args['e_dimission_date'] = datetime.datetime.strptime(sh_e_dimission_date, '%m/%d/%Y')

            #57 离职原因 e_dimission_reason
            sh_e_dimission_reason = sh.cell(rownum, 58).value
            args['e_dimission_reason'] =  sh_e_dimission_reason

            #58 个人辞职原因 e_dimission_personal_reason

            sh_e_dimission_personal_reason = sh.cell(rownum, 59).value
            args['e_dimission_personal_reason'] =  sh_e_dimission_personal_reason

            #59 离职补偿 e_dimission_compentation
            sh_e_dimission_compentation = sh.cell(rownum, 60).value
            args['e_dimission_compentation'] =  sh_e_dimission_compentation


            #创建employee
            employee.create(cr, uid, args,context=context)


    _columns = {
        'db_datas': fields.binary('Database Data'),
    }

hr_employee_import()
