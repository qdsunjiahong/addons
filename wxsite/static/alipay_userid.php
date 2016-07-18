<?php
if(!isset($_SERVER['argv'][1]))
    exit('0');

$log = "PHP RSA Encrypt:\n";

$auth_code = $_SERVER['argv'][1];
$data = array(
    'app_id' => '2016030201177117',
    'method' => 'alipay.system.oauth.token',
    'charset' => 'UTF-8',
    'sign_type' => 'RSA',
    'version' => '1.0',
    'timestamp' => date('Y-m-d H:i:s'),
    'grant_type' => 'authorization_code',
    'code' => $auth_code,
);

//排序、拼接字符串
$data_str = '';
ksort($data);
foreach($data as $key=>$val)
    $data_str .= $data_str==''?$key.'='.$val:'&'.$key.'='.$val;

$log .= '  Str Query:'.$data_str."\n";

//签名
$encryptData = '';
$privateKey = openssl_pkey_get_private(file_get_contents('/site/apps/saas-7/addons-extra/wxsite/static/rsa_private_key.pem'));
openssl_sign($data_str, $encryptData, $privateKey);
$encryptData = base64_encode($encryptData);

$data['sign'] = $encryptData;

$log .= '  Sign:'.$encryptData."\n";

//发送请求
$url = 'https://openapi.alipay.com/gateway.do';
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_HEADER, 0);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
$ret = curl_exec($ch)."\n";
$ret_json = iconv('gbk', 'utf-8', $ret);

//解析json得到支付宝user_id
$ret_arr = (array)json_decode($ret_json);
$ret_inner_arr = (array)$ret_arr['alipay_system_oauth_token_response'];

$rets = array(
    'alipay_user_id' => $ret_inner_arr['alipay_user_id'],
    'access_token' => $ret_inner_arr['access_token'],
    'sign' => $encryptData,
);
echo json_encode($rets);

$fhandle = fopen('/var/log/odoo/odoo-saas7_log.log', 'a');
fwrite($fhandle, $log."\n");
fclose($fhandle);
?>
