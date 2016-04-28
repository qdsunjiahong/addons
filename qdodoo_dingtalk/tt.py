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


corpid = 'ding9fdc4501ed0ed880'
secrect = 'TZbQ31u_9vWZ9d3rS7hev6WVU78NgcugbNTE7xcGM9FYCG6mNu14YrQFGtwC697P'
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
