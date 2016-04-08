<?php
if(!isset($_SERVER['argv'][1]))
    exit('0');

$access_token = $_SERVER['argv'][1];
$data = array(
    'method' => 'alipay.user.userinfo.share',
    'timestamp' => date('Y-m-d H:i:s'),
    'app_id' => '2016030201177117',
    'auth_token' => $access_token,
    'charset' => 'UTF-8',
    'version' => '1.0',
    'sign_type' => 'RSA',
);

//排序、拼接字符串
$data_str = '';
ksort($data);
foreach($data as $key=>$val)
    $data_str .= $data_str==''?$key.'='.$val:'&'.$key.'='.$val;

//签名
$encryptData = '';
$privateKey = openssl_pkey_get_private(file_get_contents('/site/apps/saas-7/addons-extra/wxsite/static/rsa_private_key.pem'));
openssl_sign($data_str, $encryptData, $privateKey);
$encryptData = base64_encode($encryptData);

$data['sign'] = $encryptData;

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
$ret_inner_arr = (array)$ret_arr['alipay_user_userinfo_share_response'];

$rets = array(
    'nick_name' => $ret_inner_arr['nick_name'],
    'city' => $ret_inner_arr['city'],
);
echo json_encode($rets);
?>
