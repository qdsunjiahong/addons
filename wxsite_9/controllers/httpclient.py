# -*- coding: utf-8 -*-
import httplib, urllib
def http_python(url, port, url2, params, lb):
    """
        与java接口交互的共通函数
        :param url 访问的IP地址
        :param port 访问的IP端口
        :param url2 访问的系统方法
        :param params 参数
        :param lb 请求方式：POST/GET
    """
    httpClient = None
    httpClient = httplib.HTTPConnection(url, port, timeout=6000)
    try:
        if lb == 'POST':
            param = urllib.urlencode(params)
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text双击查看原图ml"}
            httpClient.request(lb, url2, param, headers)
            response = httpClient.getresponse()
            return response.read()

        elif lb == 'GET':
            httpClient.request(lb, url2)
            response = httpClient.getresponse()
            return response.read()
    except Exception, e:
        return -1

    finally:
        if httpClient:
            httpClient.close()