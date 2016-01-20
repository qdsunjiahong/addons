//微信支付所需Json数据，从div层获取字符串转换为json对象
var wxpay_json = JSON.parse($('#wxpay_json').text());

//发起微信支付，该部分js只能在微信中运行
function jsApiCall(){
    WeixinJSBridge.invoke(
        'getBrandWCPayRequest',
        wxpay_json,  //微信支付所需json数据
        function(res){  //支付完成的回调函数
            WeixinJSBridge.log(res.err_msg);

            if(res.err_msg == 'get_brand_wcpay_request：ok' || res.err_msg == 'get_brand_wcpay_request:ok'){
                alert('支付完成，查看订单');
                location.href = '/shop/wx/order';  //跳转到订单管理页面
            }else{
                alert('支付失败：'+res.err_msg);
            }

            //location.href = '/shop/wx/order';  //跳转到订单管理页面
            // alert(res.err_code+res.err_desc+res.err_msg); //输出返回值
        }
    );
}

//发起微信支付的js入口
function callpay(){
    if (typeof WeixinJSBridge == "undefined"){
        if( document.addEventListener ){
            document.addEventListener('WeixinJSBridgeReady', jsApiCall, false);
        }else if (document.attachEvent){
            document.attachEvent('WeixinJSBridgeReady', jsApiCall);
            document.attachEvent('onWeixinJSBridgeReady', jsApiCall);
        }
    }else{
        jsApiCall();
    }
}