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
        fd = urllib2.urlopen(req, data=data)
        return json.loads(fd.read())

    @api.model
    def dd_hr_synchronization(self):
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
                    employee_url = "https://oapi.dingtalk.com/user/list?access_token=ACCESS_TOKEN&department_id=%s" % department_id
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
            # erp_department_dict_name = {}  # {部门id:部门名称}
            erp_department_dict = {}  # {部门名称：[员工工号]}
            erp_employee_dict_id = {}  # {员工工号:员工名称}
            erp_employee_mobile = {}  # {员工工号：员工电话}
            # erp_employee_name_dict = {}  # {员工工号：员工名称}
            for department_id in department_ids:
                dp_id = department_id.id
                dp_name = department_id.name
                # erp_department_dict_name[dp_id] = dp_name
                dp_list = erp_department_dict[dp_name] = []
                for employee_id in employee_ids:
                    ep_id = employee_id.e_no
                    ep_name = employee_id.name
                    moblie_phone = employee_id.work_phone
                    dp_id2 = employee_id.department_id.id
                    if dp_id2 == dp_id:
                        erp_employee_mobile[ep_id] = moblie_phone
                        erp_employee_dict_id[ep_id] = ep_name
                        # erp_employee_name_dict[er]
                        dp_list.append(employee_id.id)

            for erp_department_l in erp_department_dict:
                erp_dp_id = erp_department_l  # erp部门名称
                erp_dp_list = erp_department_dict.get(erp_dp_id)  # 成员工号列表
                if erp_department_l in dd_dpmt_dict:
                    print 766645343
                    for erp_dp_l in erp_dp_list:
                        if erp_dp_l not in dd_dpmt_dict.get(erp_department_l):
                            employee_url = "https://oapi.dingtalk.com/user/create?access_token=%s" % access_token
                            data = {
                                'access_token': access_token,
                                'name': erp_employee_dict_id.get(erp_dp_l),
                                'department': dd_dpmt_dict_id.get(erp_department_l),
                                'mobile': erp_employee_mobile.get(erp_dp_l),
                                'jobnumber': erp_dp_l
                            }
                            self.url_post(employee_url, data)
                        else:
                            employee_update_url = "https://oapi.dingtalk.com/user/update?access_token=%s" % access_token
                            data = {
                                'access_token': access_token,
                                'userid': userid_dict.get(erp_dp_l),
                                'name': erp_employee_dict_id.get(erp_dp_l),
                                'department': dd_dpmt_dict_id.get(erp_department_l),
                                'mobile': erp_employee_mobile.get(erp_dp_l),
                                'jobnumber': erp_dp_l
                            }
                            self.url_post(employee_update_url, data)
                else:
                    print 777777777
                    department_create_url = "https://oapi.dingtalk.com/department/create?access_token=%s" % access_token
                    data = {
                        'access_token': access_token,
                        'name': erp_department_l,
                        'parentid': parent_id_dict.get(erp_department_l),
                    }
                    req = self.url_post(department_create_url, data)
                    if req.get('errcode', '') == 0:
                        create_id = req.get('id')
                        for erp_dp_l in erp_dp_list:
                            employee_url = "https://oapi.dingtalk.com/user/create?access_token=%s" % access_token
                            data = {
                                'access_token': access_token,
                                'name': erp_employee_dict_id.get(erp_dp_l),
                                'department': create_id,
                                'mobile': erp_employee_mobile.get(erp_dp_l),
                                'jobnumber': erp_dp_l
                            }
                            self.url_post(employee_url, data)
            print '222222', 'end'
