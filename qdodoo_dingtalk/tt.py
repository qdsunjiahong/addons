# encoding:utf-8
import urllib2
import json


def url_get(url):
    req = urllib2.Request(url)
    req_dict = json.loads(urllib2.urlopen(req).read())
    return req_dict


def url_post(url, data):
    req = urllib2.Request(url, headers={"Content-Type": "application/json", 'charset': 'UTF-8'})
    fd = urllib2.urlopen(req, data=data)
    return json.loads(fd.read())


corpid = 'dinge0b8fc92eb965404'
secrect = 'MkKb_QDrtkwigaBar13AHo51xQLcJdnzLFiE_giow1kXeQUWLDH0K-1kC9gup7Zx'
token_url = 'https://oapi.dingtalk.com/gettoken?corpid=%s&corpsecret=%s' % (corpid, secrect)
access_token_dict = url_get(token_url)
access_token = access_token_dict.get('access_token', 0)
department_create_url = "https://oapi.dingtalk.com/department/create?access_token=%s" % access_token
data = {
    'access_token': access_token,
    'name': '测试部门',
    'parentid': 1,
}
req = url_post(department_create_url, json.dumps(data))
