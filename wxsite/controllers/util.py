# -*- coding: utf-8 -*-
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_v1_5
import urllib2
import urllib
import json
from Crypto import Random

try:
    import hashlib
    md5_constructor = hashlib.md5
    md5_hmac = md5_constructor
    sha_constructor = hashlib.sha1
    sha_hmac = sha_constructor
except ImportError:
    import md5
    md5_constructor = md5.new
    md5_hmac = md5
    import sha
    sha_constructor = sha.new
    sha_hmac = sha

from Crypto.Hash import SHA
from Crypto.Signature import PKCS1_v1_5 as pk
import base64

import sys
import types
reload(sys)
sys.setdefaultencoding('utf8')

md5 = md5_constructor

def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    if not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s

def params_filter(params):
    ks = params.keys()
    ks.sort()
    newparams = {}
    prestr = ''
    for k in ks:
        v = params[k]
        k = smart_str(k, 'utf-8')
        if k not in ('sign') and v != '':
            newparams[k] = smart_str(v, 'utf-8')
            prestr += '%s=%s&' % (k, newparams[k])
    prestr = prestr[:-1]
    return newparams, prestr

def build_mysign(prestr, key, sign_type = 'MD5'):
    if sign_type == 'MD5':
        return md5(prestr + '&key=' +key).hexdigest().upper()
    return ''

def sort(mes):
    '''
    作用类似与java的treemap,
    取出key值,按照字母排序后将value拼接起来
    返回字符串
    '''
    _par = []

    keys=mes.keys()
    keys.sort()
    for v in keys:
        _par.append(str(mes[v]))
    sep=''
    message=sep.join(_par)
    return message

def sign(signdata,key):
    '''
    @param signdata: 需要签名的字符串
    '''

    h=SHA.new(signdata)
    signer = pk.new(key)
    signn=signer.sign(h)
    signn=base64.b64encode(signn)
    return signn

'''
aes加密base64编码
'''
def aes_base64_encrypt(data,key):

    """
    @summary:
        1. pkcs7padding
        2. aes encrypt
        3. base64 encrypt
    @return:
        string
    """
    cipher = AES.new(key)
    return base64.b64encode(cipher.encrypt(_pkcs7padding(data)))

def _pkcs7padding(data):
    """
    对齐块
    size 16
    999999999=>9999999997777777
    """
    size = AES.block_size
    count = size - len(data)%size
    if count:
        data+=(chr(count)*count)
    return data

'''
rsa加密
'''
def rsa_base64_encrypt(data,key):
    '''
    1. rsa encrypt
    2. base64 encrypt
    '''
    cipher = PKCS1_v1_5.new(key)
    return base64.b64encode(cipher.encrypt(data))

def doPost(url,values):
    '''
    post请求
    参数URL
    字典类型的参数
    '''
    req = urllib2.Request(url)
    data = urllib.urlencode(values)
    res = urllib2.urlopen(req, data)
    ret = res.read()
    return ret

'''
rsa解密
'''
def rsa_base64_decrypt(data,key):
    '''
    1. base64 decrypt
    2. rsa decrypt
    示例代码

    key = RSA.importKey(open('privkey.der').read())
    >>>
    >>> dsize = SHA.digest_size
    >>> sentinel = Random.new().read(15+dsize) # Let's assume that average data length is 15
    >>>
    >>> cipher = PKCS1_v1_5.new(key)
    >>> message = cipher.decrypt(ciphertext, sentinel)
    >>>
    >>> digest = SHA.new(message[:-dsize]).digest()
    >>> if digest==message[-dsize:]: # Note how we DO NOT look for the sentinel
    >>> print "Encryption was correct."
    >>> else:
    >>> print "Encryption was not correct."
    '''
    cipher = PKCS1_v1_5.new(key)
    return cipher.decrypt(base64.b64decode(data), Random.new().read(15+SHA.digest_size))

def _depkcs7padding(data):
    """
    反对齐
    """
    newdata = ''
    for c in data:
        if ord(c) > AES.block_size:
            newdata+=c
    return newdata

def base64_aes_decrypt(self,data,key):
    """
    1. base64 decode
    2. aes decode
    3. dpkcs7padding
    """
    cipher = AES.new(key)
    return _depkcs7padding(cipher.decrypt(base64.b64decode(data)))

'''
对返回结果进行解密后输出
'''
def result_decrypt(result,key):
    '''
    1、返回的结果json传给data和encryptkey两部分，都为加密后的
    2、用商户私钥对encryptkey进行RSA解密，生成解密后的encryptkey。参考方法：rsa_base64_decrypt
    3、用解密后的encryptkey对data进行AES解密。参考方法：base64_aes_decrypt
    '''
    result=json.loads(result)
    kdata=result['data']
    kencryptkey=result['encryptkey']
    print '返回的加密后的data='+kdata
    print '返回的加密后的encryptkey='+kencryptkey
    cryptkey=rsa_base64_decrypt(kencryptkey,key)
    print '解密后的encryptkey='+cryptkey
    rdata=base64_aes_decrypt(kdata,cryptkey)
    print '解密后的data='+rdata
    return rdata
