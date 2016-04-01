# encoding:utf-8

from openerp import models, fields, api, _
import urllib2
import json
from openerp.exceptions import except_orm

department_create_url = "https://oapi.dingtalk.com/department/create?access_token=%s"


class qdodoo_department_auto(models.Model):
    """
    计划的动作，定时定点执行方法：同步钉钉与erp系统的部门与员工
    """
    _name = 'qdodoo.department.auto'
    _description = 'qdodoo.department.auto'

    def url_get(self, url):
        req = urllib2.Request(url)
        req_dict = json.loads(urllib2.urlopen(req).read())
        return req_dict

    def url_post(self, url, data):
        req = urllib2.Request(url, headers={"Content-Type": "application/json", 'charset': 'UTF-8'})
        fd = urllib2.urlopen(req, data=json.dumps(data))
        return json.loads(fd.read())

    def department_create_item2(self, key, department_name_list, access_token, department_name_id,
                                erp_department_parentid):
        # key :部门名称,value：上级部门名称
        value = erp_department_parentid.get(key, '')
        if value in department_name_list:
            if key not in department_name_list:
                parent_id = department_name_id.get(value)
                data = {
                    'access_token': access_token,
                    'name': key,
                    'parentid': parent_id
                }
                req = self.url_post(department_create_url % access_token, data)
                if req.get('errcode') == 0:
                    return {'key': key, 'pa_id': req.get('id')}
        else:
            self.department_create_item2(value, department_name_list, access_token, department_name_id,
                                         erp_department_parentid)

    def department_create_item1(self, erp_department_list, access_token, department_name_id, erp_department_parentid,
                                department_name_list):
        for key in erp_department_list:
            req = self.department_create_item2(key, department_name_list, access_token, department_name_id,
                                               erp_department_parentid)
            if req:
                erp_department_list.remove(req.get('key'))
                department_name_list.append(req.get('key'))
                department_name_id[key] = req.get('pa_id')
            else:
                erp_department_list.remove(key)
            if erp_department_list:
                self.department_create_item1(erp_department_list, access_token, department_name_id,
                                             erp_department_parentid,
                                             department_name_list)
        return {'department_name_list': department_name_list, 'department_name_id': department_name_id}

    def get_confiure(self):

        corpid = self.env["ir.config_parameter"].get_param("qdoo.dd.corpid")
        secrect = self.env["ir.config_parameter"].get_param("qdoo.dd.secrect")
        return (corpid, secrect)

    @api.model
    def dd_hr_synchronization(self):
        """
        每天自动同步erp与钉钉员工信息
        """
        # 获取access_token

        corpid, secrect = self.get_confiure()
        token_url = 'https://oapi.dingtalk.com/gettoken?corpid=%s&corpsecret=%s' % (corpid, secrect)
        access_token_dict = self.url_get(token_url)
        access_token = ""
        try:
            access_token = access_token_dict.get('access_token', '')
        except:
            pass
        today = fields.Date.today()
        start_time = today + " 00:00:01"
        end_time = today + " 23:59:59"
        ###### 获取钉钉部门列表########
        dd_department_get = "https://oapi.dingtalk.com/department/list?access_token=%s" % access_token
        department_info_dict = self.url_get(dd_department_get)
        department_list = department_info_dict.get('department', [])
        department_name_id = {}  # {部门名称:部门id}
        department_name_parentid = {}  # {部门名称:父部门id}
        department_name_list = []  # 部门名称列表
        for department_l in department_list:
            department_name = department_l.get('name')
            department_id = department_l.get('id')
            parentid = department_l.get('parentid', False)
            department_name_id[department_name] = department_id
            department_name_parentid[department_name] = parentid
            department_name_list.append(department_name)
        #####获取ERP系统部门列表
        erp_department_list = []
        erp_department_parentid = {}  # {部门名称:父部门名称}
        erp_department_ids = self.env['hr.department'].search(
            [('create_date', '>=', start_time), ('create_date', '<=', end_time), ('parent_id', '!=', False)])

        for erp_department_id in erp_department_ids:
            erp_department_list.append(erp_department_id.name)
            erp_department_parentid[erp_department_id.name] = erp_department_id.parent_id.name or ''
        ####循环对比钉钉与erp部门信息######
        req = self.department_create_item1(erp_department_list, access_token, department_name_id,
                                           erp_department_parentid,
                                           department_name_list)
        department_name_id = req.get('department_name_id')
        ####update员工信息##########
        # 获取当天修改过的ERP员工列表
        employee_ids = self.env['hr.employee'].search(
            [('write_date', '>=', start_time), ('write_date', '<=', end_time)])
        for employee_id in employee_ids:
            dd_userid = employee_id.dd_user_id
            user_name = employee_id.name
            department_id = department_name_id.get(employee_id.department_id.name)
            phone_number = employee_id.mobile_phone
            data = {
                'access_token': access_token,
                'userid': dd_userid,
                'name': user_name,
                'department': [department_id],
                'mobile': phone_number,
            }
            # active 为true,更新
            if employee_id.active:
                user_update = "https://oapi.dingtalk.com/user/update?access_token=%s" % access_token
                self.url_post(user_update, data)
            # active 为False,删除
            else:
                data = {
                    'access_token': access_token,
                    'userid': dd_userid,
                }
                user_delete = 'https://oapi.dingtalk.com/user/delete?access_token=%s&userid=%s' % (
                    access_token, dd_userid)
                self.url_post(user_delete, data)

        #######新建员工#########
        # 获取当天所有新建的erp员工
        employee_ids_create = self.env['hr.employee'].search(
            [('create_date', '>=', start_time), ('create_date', '<=', end_time)])
        user_create = "https://oapi.dingtalk.com/user/create?access_token=%s" % access_token
        for employee_id_create in employee_ids_create:
            department_id = department_name_id.get(employee_id_create.department_id.name)
            data = {
                'access_token': access_token,
                'name': employee_id_create.name,
                'department': [department_id],
                'mobile': employee_id_create.mobile_phone
            }
            res = self.url_post(user_create, data)
            userid = res.get('userid', False)
            if userid:
                employee_id_create.wirte({'dd_user_id': userid})

    @api.multi
    ####初始化方法########
    def dd_hr_synchronization2(self):
        """
        以手机号码为唯一标识
        """

        # 获取access_token

        corpid, secrect = self.get_confiure()
        token_url = 'https://oapi.dingtalk.com/gettoken?corpid=%s&corpsecret=%s' % (corpid, secrect)
        access_token_dict = self.url_get(token_url)
        access_token = ""
        try:
            access_token = access_token_dict.get('access_token', '')
        except:
            pass
        ###### 获取钉钉部门列表########
        if not access_token:
            raise except_orm(_(u'警告'), _(u'请检查钉钉配置'))
        dd_department_get = "https://oapi.dingtalk.com/department/list?access_token=%s" % access_token
        department_info_dict = self.url_get(dd_department_get)
        department_list = department_info_dict.get('department', [])
        #######部门信息########
        department_name_id = {}  # {部门名称:部门id}
        department_name_parentid = {}  # {部门名称:父部门id}
        department_name_list = []  # 部门名称列表
        ########员工信息########
        dd_user_mobile_list = []  # 钉钉员工电话列表
        dd_user_mobile_dict = {}  # {电话：userid}
        ########循环部门列表#########
        for department_l in department_list:
            department_name = department_l.get('name')
            department_id = department_l.get('id')
            parentid = department_l.get('parentid', False)
            department_name_id[department_name] = department_id
            department_name_parentid[department_name] = parentid
            department_name_list.append(department_name)
            # 获取所有部门成员信息列表
            dd_users_get = "https://oapi.dingtalk.com/user/list?access_token=%s&department_id=%s" % (
                access_token, department_id)
            dd_user_list = self.url_get(dd_users_get).get('userlist', [])
            for dd_user in dd_user_list:
                mobile = dd_user.get('mobile')
                dd_userid = dd_user.get('id')
                dd_user_mobile_list.append(mobile)
                dd_user_mobile_dict[mobile] = dd_userid
        #####获取ERP系统部门列表
        erp_department_list = []
        erp_department_parentid = {}  # {部门名称:父部门名称}
        erp_department_ids = self.env['hr.department'].search([('parent_id', '!=', False)])

        for erp_department_id in erp_department_ids:
            erp_department_list.append(erp_department_id.name)
            erp_department_parentid[erp_department_id.name] = erp_department_id.parent_id.name or ''
        ####循环对比钉钉与erp部门信息######
        req = self.department_create_item1(erp_department_list, access_token, department_name_id,
                                           erp_department_parentid,
                                           department_name_list)
        department_name_id = req.get('department_name_id')
        ####erp员工信息##########
        erp_user_mobile_list = []  # erp员工列表
        # 获取erp所有员工列表
        employee_ids = self.env['hr.employee'].search([('active', '!=', True)])
        for employee_id in employee_ids:
            user_name = employee_id.name
            department_id = department_name_id.get(employee_id.department_id.name)
            phone_number = employee_id.mobile_phone
            ####如果存在，更新员工信息
            if phone_number in dd_user_mobile_list:
                dd_user_id = dd_user_mobile_dict.get(phone_number)
                data = {
                    'access_token': access_token,
                    'userid': dd_user_id,
                    'name': user_name,
                    'department': [department_id],
                    'mobile': phone_number,
                }
                user_update = "https://oapi.dingtalk.com/user/update?access_token=%s" % access_token
                self.url_post(user_update, data)
                erp_user_mobile_list.append(phone_number)
                employee_id.write({'dd_user_id': dd_user_id})
            # 创建
            else:
                data = {
                    'access_token': access_token,
                    'name': user_name,
                    'department': [department_id],
                    'mobile': phone_number
                }
                user_create = 'https://oapi.dingtalk.com/user/create?access_token=%s' % access_token
                req_create = self.url_post(user_create, data)
                userid = req_create.get('userid', False)
                if userid:
                    employee_id.wirte({'dd_user_id': userid})
                    erp_user_mobile_list.append(phone_number)

        ######删除########
        for dd_user_mobile_l in dd_user_mobile_list:
            if dd_user_mobile_l not in erp_user_mobile_list:
                userid = dd_user_mobile_dict.get(dd_user_mobile_l)
                user_delete = "https://oapi.dingtalk.com/user/delete?access_token=%s&userid=%s" % (access_token, userid)
                self.url_get(user_delete)
