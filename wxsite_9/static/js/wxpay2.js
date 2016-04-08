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
                alert('支付失败：err_code:'+res.err_code+', err_desc:'+res.err_desc+', err_msg:'+res.err_msg);
            }

            //location.href = '/shop/wx/order';  //跳转到订单管理页面
            // alert(res.err_code+res.err_desc+res.err_msg); //输出返回值
        }
    );
}

//发起微信支付的js入口
function callpay(){
    var deskNo = $('input[name="deskno"]').val();  //桌号
    var orderNote = $('input[name="onote"]').val();  //备注/要求
    var taste = $('select[name="taste"]').val();  //备注/要求
    var res_order_id = wxpay_json.res_order_id;  //商户订单号
    alert('桌号：'+deskNo+', 备注：'+orderNote+', 要求：'+taste+', 单号：'+res_order_id)
    if (deskNo == ''){
        alert("请输入桌号！");
    }else{
        //更新订单中信息
        $.ajax({
                url: '/onchange/order',  //Ajax请求地址
                type: 'POST',
                data: {
                    deskNo: deskNo,
                    orderNote: orderNote,
                    res_order_id_new: res_order_id,
                    taste: taste
                }}).done(function(msg){
                    alert('ajax done!');
                    if(msg == '1'){  //处理成功
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
                    }else{
                        alert("操作失败，请联系管理员！");
                    }
                });
    }

}