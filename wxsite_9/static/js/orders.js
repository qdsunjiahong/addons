//取消订单
$('a.ocancel').click(function(){
    var orderId = $(this).attr('id');  //单号
    var pidID = $(this).attr('pid');  //单号

    //Ajax请求示例
    window.location.href = '/shop/wx/wxpay?oid='+orderId+'&money=' + pidID
    return true;


});
