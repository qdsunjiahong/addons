# -*- coding: utf-8 -*-
# #############################################################################
#
# Copyright (C) 2014 Rainsoft  (<http://www.agilebg.com>)
#    Author:Kevin Kong <kfx2007@163.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from datetime import datetime


class hm_employee(models.Model):
    _inherit = 'hr.employee'

    e_job_status = fields.Selection(string='在职状态',compute='_get_job_status',selection=[('on',u'在职'),('off',u'离职')])
    e_email = fields.Char(string=u"外部电子邮箱")
    e_no = fields.Char(string="Employee No")
    e_name = fields.Char(string="English Name")
    e_grade = fields.Many2one('hm.grade', string='Grade')
    e_emergency_contact = fields.Char(string="Emergency Contact")
    e_emergency_relation = fields.Char(string="Emergency Relation")
    e_emergency_phone = fields.Char(string="Emergency Phone")
    e_personal_phone = fields.Char(string="Personal Phone")
    e_age = fields.Char(string=u"年龄", compute='_get_age')
    e_hukou_type = fields.Selection(string="HuKou Type", selection=[('Loc', u'本地'), ('Out', u'外地')])
    e_hukou_location = fields.Selection(string='HuKou Location', selection=[('urban', u'城镇'), ('rural', u'农村')])
    e_address = fields.Char(string="Address")
    e_parttime_job = fields.Many2many('hr.job')
    e_parttime_department = fields.Many2many('hr.department')
    e_hukou_address = fields.Char(string="HuKou Address")
    e_rent = fields.Boolean(string="Rent")
    e_recruit_date = fields.Date(string="Recruit Date")
    e_job_date = fields.Date(string="Job Date")
    e_work_age = fields.Char(string="Work Age", compute='_get_workage')
    gongling = fields.Integer(string="gongling", compute='_get_workage')
    e_contract_No = fields.Many2one('hr.contract',string='Contract',compute="_get_contract")
    e_contract_type = fields.Many2one('hr.contract.type', string="Contract Type", compute='_get_contract')
    e_workhour_type = fields.Selection(string="Workhour Type",
                                       selection=[('fix', u'固定'), ('nofix', u'不定'), ('all', u'综合')],compute='_get_contract')
    e_hire_type = fields.Selection(string='Hire Type',
                                   selection=[('probation', u'试用'), ('hour', u'钟点工'), ('back', u'返聘'),
                                              ('official', u'正式')])
    e_contract_start = fields.Date(string='Contract Begin',compute='_get_contract',required=True)
    e_contract_stop = fields.Date(string="Contract End",compute="_get_contract",required=True)
    e_probation_length = fields.Char(string='Probation Length')
    e_ss_date = fields.Date(string="Social Society Fund")
    e_ss_base = fields.Float(string="Social Society Base")
    e_accident_insurance_stop = fields.Date(string='Accident Insurance End')
    e_ss_no = fields.Char(string='Social Society No')
    e_provident_fund_date = fields.Date(string="Provident Fund Date")
    e_provident_fund_base = fields.Float(string="Provident Fund Base")
    e_provident_fund_no = fields.Char(string="Provident Fund No")
    e_education_backgroud = fields.Char(string='1st Education Backgroud')
    e_major = fields.Char(string='Major')
    e_university = fields.Char(string='University')
    e_graduated_date = fields.Date(string='Graduated Date')
    e_highest_education = fields.Char(string='Highest Education')
    e_highest_major = fields.Char(string='Highest Major')
    e_certificated_date = fields.Date(string='Ceritificated Date')
    e_certification = fields.Char(string='Certification')
    e_skill_certification = fields.Char(string="Skill Certification")
    e_health_certification = fields.Char(string='Health Certification')
    e_dimission_date = fields.Date(string='Dimission Date')
    e_dimission_reason = fields.Selection(string='Dimission Reason', selection=[('fire', u'辞退'), ('quit', u'辞职')])
    e_dimission_personal_reason = fields.Text(string='Personal Reason')
    e_dimission_compentation = fields.Char(string='Dimission Compentation ')
    e_dimission_labor_disputes =  fields.Selection(string='劳动纠纷',selection=[('none', u'无'),('arbitration',u'仲裁'),('prosecution',u'起诉')])
    e_state = fields.Selection(string="State", selection=[('keep', u'在职'), ('leave', u'离职')])

    ##后增加
    e_file_transfer_date = fields.Date(string="档案转总部日期")
    e_gap = fields.Char(string="缺项内容")
    ##继承的字段
    e_gender = fields.Selection(string='gender', compute='_get_gender', selection=[('male', u'男性'), ('female', u'女性'),('unknown',u'非男非女')])
    e_birthday = fields.Date(string=u"出生日期", compute='_get_birthday')

    company_sign = fields.Many2one('res.partner', string='签订合同公司', related='contract_id.company_sign',compute='_get_contract')

    e_ss_type = fields.Selection(string='社保缴纳方式',
                                 selection=[('agent', u'代理'), ('company', u'公司缴纳'), ('personal', u'个人缴纳')])
    e_ss_main = fields.Char(string='社保缴纳主体')


    #账户信息
    bank1 = fields.Char(string = '开户行1')
    bank1_no = fields.Char(string="银行卡号1")

    bank2 = fields.Char(string = '开户行2')
    bank2_no = fields.Char(string="银行卡号2")

    edu_record_count = fields.Integer(string=u'学历记录数', compute='_edu_record_count')
    certificate_count = fields.Integer(string=u'证书记录数', compute='_certificate_count')
    work_record_count = fields.Integer(string=u'工作记录数', compute='_work_record_count_count')
    contract_count2 = fields.Integer(string=u'合同数')

    _defaults={
            "e_contract_start":datetime.now(),
            "e_contract_stop":datetime.now(),
            "e_workhour_type":"fix",
            }

    @api.one
    def _get_contract(self):
        contracts=self.env['hr.contract'].search([('employee_id','=',self.id)])
        contracts = sorted(contracts,key=lambda x:x.date_start,reverse=True)
        if len(contracts):
            self.e_contract_type = contracts[0].type_id
            self.company_sign = contracts[0].company_sign
            self.e_contract_start=contracts[0].date_start
            self.e_contract_stop=contracts[0].date_end
            self.e_contract_No = contracts[0]
            self.e_workhour_type = contracts[0].work_hours
        else:
            self.e_contract_start = datetime.now()
            self.e_contract_stop = datetime.now()

    def _work_record_count_count(self):
        '''
            计算 工作记录数
        :return:
        '''
        work_record = self.env['hr.work.record']
        self.work_record_count = work_record.search_count([('employee_id','=',self.id)])

    def _certificate_count(self):
        '''
            计算 证书记录数
        :return:
        '''
        Certificate = self.env['hr.certificate']
        self.certificate_count = Certificate.search_count([('employee_id','=',self.id)])


    def _edu_record_count(self):
        '''
            计算 学历记录数量
        :return:
        '''
        Education_record = self.env['hr.edu.record']
        self.edu_record_count = Education_record.search_count([('employee_id','=',self.id)])

    def _get_job_status(self):
        '''
        获取在职状态
        :return:
        '''
        if self.e_dimission_date:
            self.e_job_status = 'off'
        else:
            self.e_job_status = 'on'


    def _get_birthday(self):
        if self.identification_id:
            if len(self.identification_id) == 18:
                try:
                    birth_date = datetime.strptime(self.identification_id[6:14], '%Y%m%d')
                    self.e_birthday = birth_date
                except:
                    self.e_birthday=datetime.now()
            else:
                 self.e_birthday = None
        else:
             self.e_birthday = None

    def _get_age(self):
        if self.identification_id:
            if len(self.identification_id) == 18:
                try:
                    birth_date = datetime.strptime(self.identification_id[6:14], '%Y%m%d')
                    age = datetime.now().year - birth_date.year
                    self.e_age = age
                except:
                    self.e_age = 0;
            else:
                self.e_age = 0
        else:
            self.e_age = 0


    def _get_gender(self):
        if self.identification_id:
            if len(self.identification_id) == 18:
                sex = self.identification_id[-2]
                try:
                    if sex.lower() == 'x':
                        self.e_gender = 'female'
                    elif int(sex) % 2 == 0:
                        self.e_gender = 'female'
                    else:
                        self.e_gender = 'male'
                except:
                    self.e_gender = 'unknown'
            else:
                self.e_gender = 'male'
        else:
            self.e_gender = 'male'


    def _get_workage(self):
        if self.e_recruit_date:
            period = datetime.now() - datetime.strptime(self.e_recruit_date, '%Y-%m-%d')
            year = period.days/365
            month = period.days%365/30
            self.e_work_age = str(year)+"年"+str(month)+"月"
            self.gongling=year
        else:
            self.e_work_age = "0"
            self.gongling = "0"




class hr_contract(models.Model):
    '''
        继承自　hr_contract.hr.contract
    '''
    _inherit = 'hr.contract'

    company_sign = fields.Many2one('res.partner', string='签订合同公司')
    work_address = fields.Char(string='工作地点')
    work_hours = fields.Selection(string="Workhour Type",
                                       selection=[('fix', u'固定'), ('nofix', u'不定'), ('all', u'综合')])
    other_welfare = fields.Char(string='其他福利')
    other = fields.Text(string='其他')

    #薪资信息
    ##基本工资
    base_wage = fields.Float(string='金额')
    base_wage_condition = fields.Char(string='计发条件')
    base_wage_date = fields.Char(string='计薪日期')
    ##职务工资
    duty_wage = fields.Float(string='金额')
    duty_wage_condition = fields.Char(string='计发条件')
    duty_wage_date = fields.Char(string='计薪日期')
    ##工龄工资
    age_wage = fields.Float(string='金额')
    age_wage_condition = fields.Char(string='计发条件')
    age_wage_date = fields.Char(string='计薪日期')
    ##岗位技能工资
    post_wage = fields.Float(string='金额')
    post_wage_condition = fields.Char(string='计发条件')
    post_wage_date = fields.Char(string='计薪日期')


    #福利信息

    #绩效考核约定
    performance = fields.Binary(string=u'适用绩效方案')
    performance_type = fields.Selection(string=u'绩效类型',selection=[('salary',u'年薪绩效'),('business',u'业务提成'),('standard',u'标准绩效')])
    performance_amout = fields.Float(string=u'绩效额度')
    performance_paul_salary = fields.Float(string=u'保底年薪')



class hr_job(models.Model):
    '''
        继承自　hr.hr.job
    '''
    _inherit = 'hr.job'

    job_no = fields.Char(string=u'职位编号')
    #任职资格
    education = fields.Char(string=u'教育/学历')
    edu_other = fields.Text(string=u'其他')
    #岗位职责
    positon_power = fields.Char(string=u'职责/权限')
    positon_content = fields.Char(string=u'工作内容')
    #胜任考核
    exam_answer = fields.Char(string=u'考核要求')
    exam_type  = fields.Char(string=u'考核形式')
    exam_cycle = fields.Char(string=u'考核周期')


class hr_edu_record(models.Model):
    '''
        学历记录
    '''
    _name = 'hr.edu.record'
    _description ='Education Record'
    _order = 'graduate_date'

    employee_id = fields.Many2one('hr.employee', string=u'员工')
    degree = fields.Many2one('hr.recruitment.degree',string='Degree')
    graduate_date =fields.Date(string=u'毕业日期')
    graduate_school = fields.Char(string=u'学校')
    graduate_professional = fields.Char(string=u'专业')


class hr_certificate(models.Model):
    '''
        证书记录
    '''
    _name = 'hr.certificate'
    _description = 'Certificate'

    employee_id = fields.Many2one('hr.employee', string=u'员工')
    name = fields.Char(string=u'证书名称')
    type = fields.Char(string=u'证书类型')
    stop_date = fields.Date(string=u'到期时间')

class hr_work_record(models.Model):
    '''
        工作记录
    '''
    _name = 'hr.work.record'
    _description = 'Work Record'

    employee_id = fields.Many2one('hr.employee', string=u'员工')
    stop_date = fields.Date(string=u'终止时间')
    start_date = fields.Date(string=u'起始时间')
    name = fields.Char(string=u'单位名称')
    work_post = fields.Char(string=u'工作岗位')
    type = fields.Selection(string=u'工作记录类型',selection=[('in',u'内部'),('out', u'外部')])
