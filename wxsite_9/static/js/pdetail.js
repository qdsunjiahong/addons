//点击“现在购买”按钮，添加购物车并跳转
$('#tobuy').click(function(){
    var productID = $('#tobuy').attr('pid');
    //已加过的不再加——当然，也可以重复多加几份
    if($('#tobuy').text()=='已添加'){
        return true;
    }
    $('#tobuy').text('添加中...');

    //加入购物车的ajax示例
    $.ajax({
            url: '/ajax/addtocart',  //Ajax请求地址
            type: 'POST',
            data: {
                pid: productID,
                num: 1
            }}).done(function(msg){
                if(msg == '1'){  //处理成功
                    $('#tobuy').text('已添加');
                    $('div.cart-num').text(msg.cartNum);
                    location.href='/shop/wx/product/'+ productID;
                }else{
                    alert("购买失败，请刷新页面后重试！");
                }
            })

    //此操作通常由ajax处理，此处仅模仿
    //$(this).text('已添加');
    //$('div.cart-num').text(parseInt($('div.cart-num').text())+1+'');
    //location.href = '/shop/wx/car';
    return true;


});