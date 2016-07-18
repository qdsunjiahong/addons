//发起微信支付的js入口
$('button.pay-btn').click(function(){
    var deskNo = $('input[name="deskno"]').val();  //桌号
    var orderNote = $('input[name="onote"]').val();  //备注/要求
    var taste = $('select[name="taste"]').val();  //备注/要求
    var res_order_id = $('input[name="oid"]').val();  //商户订单号
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
                    if(msg == '1'){  //处理成功
                        document.forms['alipaysubmit'].submit();
                    }else{
                        alert("操作失败，请联系管理员！");
                    }
                });
    }

    return false;
});
