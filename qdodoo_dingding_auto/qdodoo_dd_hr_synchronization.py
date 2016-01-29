# encoding:utf-8

from openerp import models, fields, api, _
import urllib2
import json


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
    # def department_list_handle(self,department):
    #     """
    #     {跟部门名称:[{子部门名称:[....]}]}
    #     """


    @api.model
    # def dd_hr_synchronization(self):
    #     """
    #     以员工编号为唯一标识
    #     """
    #     # 获取access_token
    #     corpid = 'dinge0b8fc92eb965404'
    #     secrect = 'MkKb_QDrtkwigaBar13AHo51xQLcJdnzLFiE_giow1kXeQUWLDH0K-1kC9gup7Zx'
    #     token_url = 'https://oapi.dingtalk.com/gettoken?corpid=%s&corpsecret=%s' % (corpid, secrect)
    #     access_token_dict = self.url_get(token_url)
    #     access_token = ""
    #     try:
    #         access_token = access_token_dict.get('access_token', 0)
    #     except:
    #         pass
    #     today = fields.Date.today()
    #     start_time = today + " 00:00:01"
    #     end_time = today + " 23:59:59"
    #     # if access_token:
    #     #     # 获取钉钉部门列表
    #     #     department_url = "https://oapi.dingtalk.com/department/list?access_token=%s" % access_token
    #     #     department_info_dict = self.url_get(department_url)
    #     #     department_list = department_info_dict.get('department', [])
    #     #     dd_dpmt_dict_id = {}  # {部门名称:部门id}
    #     #     dd_dpmt_dict = {}  # {部门名称:[成员工号]}
    #     #     dd_ep_dict = {}  # {成员工号：成员名称}
    #     #     userid_dict = {}  # {成员工号：userid}
    #     #     parent_id_dict = {}  # {部门名称:父部门id}
    #     #     for department_l in department_list:
    #     #         department_id = department_l.get('id')
    #     #         department_name = department_l.get('name')
    #     #         parent_id = department_l.get('parentid')
    #     #         parent_id_dict[department_name] = parent_id
    #     #         dd_dpmt_dict_id[department_name] = department_id
    #     #         dd_dpmt_list = dd_dpmt_dict[department_name] = []
    #     #         if department_id:
    #     #             # 获取各个部门成员
    #     #             employee_url = "https://oapi.dingtalk.com/user/list?access_token=%s&department_id=%s" % (
    #     #                 access_token, department_id)
    #     #             employee_dict = self.url_get(employee_url)
    #     #             for user_l in employee_dict.get('userlist', []):
    #     #                 dd_ep_id = user_l.get('jobnumber')
    #     #                 dd_ep_name = user_l.get('name')
    #     #                 user_id = user_l.get('userid')
    #     #                 userid_dict[dd_ep_id] = user_id
    #     #                 dd_dpmt_list.append(dd_ep_id)
    #     #                 dd_ep_dict[dd_ep_id] = dd_ep_name
    #     #
    #     # # 获取当天修改过的ERP部门列表
    #     # department_ids = self.env['hr.department'].search(
    #     #     [('write_date', '>=', start_time), ('write_date', '<=', end_time)])
    #     ###### 获取钉钉部门列表########
    #     dd_department_get = "https://oapi.dingtalk.com/department/list?access_token=%s" % access_token
    #     department_info_dict = self.url_get(dd_department_get)
    #     department_list = department_info_dict.get('department', [])
    #     department_name_id = {}  # {部门名称:部门id}
    #     department_name_parentid = {}  # {部门名称:父部门id}
    #     for department_l in department_list:
    #         department_name = department_l.get('name')
    #         department_id = department_l.get('id')
    #         parentid = department_l.get('parentid', False)
    #         department_name_id[department_name] = department_id
    #         department_name_parentid[department_name] = parentid
    #     #####获取ERP系统部门列表
    #     erp_department_list = []
    #     erp_department_parentid = {}  # {部门名称:父部门名称}
    #     erp_department_ids = self.env['hr.department'].search([])
    #     for erp_department_id in erp_department_ids:
    #         erp_department_list.append(erp_department_id.name)
    #
    #     ####循环对比钉钉与erp部门信息######
    #     # 循环erp部门
    #     for erp_department_l in erp_department_list:
    #         # erp部门在钉钉里面存在
    #         data={
    #             'access_token':access_token,
    #             'name':erp_department_l,
    #             'parentid':de
    #         }
    #         if erp_department_l in department_name_id:
    #
    #     ####update员工信息##########
    #     # 获取当天修改过的ERP员工列表
    #     employee_ids = self.env['hr.employee'].search("|",
    #                                                   [('write_date', '>=', start_time), '&',
    #                                                    ('write_date', '<=', end_time),
    #                                                    ('active', '=', False)])
    #     for employee_id in employee_ids:
    #         dd_userid = employee_id.dd_user_id
    #         user_name = employee_id.name
    #         department_list = [employee_id.department_id.id]
    #         phone_number = employee_id.work_phone
    #         e_no = employee_id.e_no
    #         data = {
    #             'access_token': access_token,
    #             'userid': dd_userid,
    #             'name': user_name,
    #             'department': department_list,
    #             'mobile': phone_number,
    #             'jobnumber': e_no
    #         }
    #         # active 为true,更新
    #         if employee_id.active:
    #             user_update = "https://oapi.dingtalk.com/user/update?access_token=%s" % access_token
    #             self.url_post(user_update, data)
    #         # active 为False,删除
    #         else:
    #             user_delete = 'https://oapi.dingtalk.com/user/delete?access_token=%s&userid=%s' % (
    #                 access_token, dd_userid)
    #             self.url_post(user_delete, data)
    #
    #     #######新建员工#########
    #     # 获取当天所有新建的erp员工
    #     employee_ids_create = self.env['hr.employee'].search(
    #         [('create_date', '>=', start_time), ('create_date', '<=', end_time)])
    #     user_create = "https://oapi.dingtalk.com/user/create?access_token=%s" % access_token
    #     for employee_id_create in employee_ids_create:
    #         data = {
    #             'access_token': access_token,
    #             'name': employee_id_create.name,
    #             'department': [employee_id_create.department.id],
    #             'mobile': employee_id_create.work_phone,
    #             'jobnumber': employee_id_create.e_no
    #         }
    #         res = self.url_post(user_create, data)
    #         userid = res.get('userid', False)
    #         if userid:
    #             employee_id_create.wirte({'dd_user_id': userid})


    def dd_hr_synchronization(self):
        """
        以员工编号为唯一标识
        """
        # 获取access_token
        corpid = 'dinge0b8fc92eb965404'
        secrect = 'MkKb_QDrtkwigaBar13AHo51xQLcJdnzLFiE_giow1kXeQUWLDH0K-1kC9gup7Zx'
        token_url = 'https://oapi.dingtalk.com/gettoken?corpid=%s&corpsecret=%s' % (corpid, secrect)
        access_token_dict = self.url_get(token_url)
        access_token = ""
        try:
            access_token = access_token_dict.get('access_token', 0)
        except:
            pass
        if access_token:
            # 获取钉钉部门列表
            department_url = "https://oapi.dingtalk.com/department/list?access_token=%s" % access_token
            department_info_dict = self.url_get(department_url)
            department_list = department_info_dict.get('department', [])
            dd_dpmt_dict_id = {}  # {部门名称:部门id}
            dd_dpmt_dict = {}  # {部门名称:[成员工号]}
            dd_ep_dict = {}  # {成员工号：成员名称}
            userid_dict = {}  # {成员工号：userid}
            parent_id_dict = {}  # {部门名称:父部门id}
            for department_l in department_list:
                department_id = department_l.get('id')
                department_name = department_l.get('name')
                parent_id = department_l.get('parentid')
                parent_id_dict[department_name] = parent_id
                dd_dpmt_dict_id[department_name] = department_id
                dd_dpmt_list = dd_dpmt_dict[department_name] = []
                if department_id:
                    # 获取各个部门成员
                    employee_url = "https://oapi.dingtalk.com/user/list?access_token=%s&department_id=%s" % (
                        access_token, department_id)
                    employee_dict = self.url_get(employee_url)
                    for user_l in employee_dict.get('userlist', []):
                        dd_ep_id = user_l.get('jobnumber')
                        dd_ep_name = user_l.get('name')
                        user_id = user_l.get('userid')
                        userid_dict[dd_ep_id] = user_id
                        dd_dpmt_list.append(dd_ep_id)
                        dd_ep_dict[dd_ep_id] = dd_ep_name

            # 获取ERP部门列表
            department_ids = self.env['hr.department'].search([])
            employee_ids = self.env['hr.employee'].search([])
            erp_department_dict = {}  # {部门名称：[员工工号]}
            erp_employee_dict_id = {}  # {员工工号:员工名称}
            erp_employee_mobile = {}  # {员工工号：员工电话}
            # 循环部门
            for department_id in department_ids:
                dp_id = department_id.id  # 部门id
                dp_name = department_id.name  # 部门名称
                dp_list = erp_department_dict[dp_name] = []
                # 循环员工
                for employee_id in employee_ids:
                    ep_id = employee_id.e_no  # 员工编号
                    ep_name = employee_id.name  # 员工名称
                    moblie_phone = employee_id.work_phone  # 员工电话
                    dp_id2 = employee_id.department_id.id  # 员工部门id

                    if dp_id2 == dp_id:
                        erp_employee_mobile[ep_id] = moblie_phone
                        erp_employee_dict_id[ep_id] = ep_name
                        dp_list.append(ep_id)
            # 循环erp 部门{部门名称：[员工工号]}
            for erp_department_l in erp_department_dict:
                # erp_dp_id = erp_department_l  # erp部门名称
                erp_dp_list = erp_department_dict.get(erp_department_l)  # 成员工号列表
                # 循环钉钉部门{部门名称:[成员工号]}
                if erp_department_l in dd_dpmt_dict:
                    # 循环erp 员工列表
                    for erp_dp_l in erp_dp_list:
                        # 如果erp员工编号不在钉钉员工工号列表里，则在钉钉创建员工，反之更新员工信息
                        if erp_dp_l not in dd_dpmt_dict.get(erp_department_l):
                            employee_url = "https://oapi.dingtalk.com/user/create?access_token=%s" % access_token
                            data = {
                                'access_token': access_token,
                                'name': erp_employee_dict_id.get(erp_dp_l),
                                'department': [dd_dpmt_dict_id.get(erp_department_l)],
                                'mobile': erp_employee_mobile.get(erp_dp_l),
                                'jobnumber': erp_dp_l
                            }
                            req = self.url_post(employee_url, data)
                        else:
                            employee_update_url = "https://oapi.dingtalk.com/user/update?access_token=%s" % access_token
                            data = {
                                'access_token': access_token,
                                'userid': userid_dict.get(erp_dp_l),
                                'name': erp_employee_dict_id.get(erp_dp_l),
                                'department': [dd_dpmt_dict_id.get(erp_department_l)],
                                'mobile': erp_employee_mobile.get(erp_dp_l),
                                'jobnumber': erp_dp_l
                            }
                            req = self.url_post(employee_update_url, data)
                else:
                    department_create_url = "https://oapi.dingtalk.com/department/create?access_token=%s" % access_token
                    data = {
                        'access_token': access_token,
                        'name': erp_department_l,
                        'parentid': 1,
                    }
                    req = self.url_post(department_create_url, data)
                    if req.get('errcode', '') == 0:
                        create_id = req.get('id')
                        for erp_dp_l in erp_dp_list:
                            employee_url = "https://oapi.dingtalk.com/user/create?access_token=%s" % access_token
                            data = {
                                'access_token': access_token,
                                'name': erp_employee_dict_id.get(erp_dp_l),
                                'department': [create_id],
                                'mobile': str(erp_employee_mobile.get(erp_dp_l)),
                                'jobnumber': str(erp_dp_l)
                            }
                            req = self.url_post(employee_url, data)
