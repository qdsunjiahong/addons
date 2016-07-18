# -*- coding: utf-8 -*-
from M2Crypto import X509, EVP, RSA, ASN1
from OpenSSL.crypto import load_privatekey, FILETYPE_PEM, sign
import base64

"""
RSA私钥签名测试
"""

#待签名字符串，模拟支付宝授权用户信息获取的post串
str = 'app_id=2016030201177117&charset=UTF-8&code=4f742bb4cda24c9693a97c885325WX14&grant_type=authorization_code&method=alipay.system.oauth.token&timestamp=2016-03-04 11:25:40&version=1.0'
rsa_private_key = load_privatekey(FILETYPE_PEM, open('rsa_private_key.pem').read())
rsa_private_sign = sign(rsa_private_key, str, 'sha1')
rsa_private_sign = base64.b64encode(rsa_private_sign)

#签名结果应该是
print rsa_private_sign
print 'SmIDqolleoftu35AFQ3nBBxo+hwIEoUoL2wJ2uSdCiBKaj0Myh9OW8/NfIlHsJMWEH+VoVDeI6mlqAN7enWF6CtvF8NUpK6kP3klNFg3CtgKY0oHhIDKeopX0CHAMbrqzBwAlX99coATH4nATiz8jP++5H0DuuInN4fS5ELUmeg='