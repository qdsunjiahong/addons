//菜品加入购物车
$('.tocart').click(function(){
    var productID = $(this).attr('id');
    
    //已加过的不再加——当然，也可以重复多加几份
    if($(this).text()=='已添加'){
        return true;
    }

    $(this).addClass('add-cart-waiting');

    //加入购物车的ajax示例
    $.ajax({
            url: '/ajax/addtocart',  //Ajax请求地址
            type: 'POST',
            data: {
                pid: productID,
                num: 1
            }}).done(function(msg){
                if(msg == '1'){  //处理成功
                    $(this).text('已添加');
                    $('div.cart-num').text(parseInt($('div.cart-num').text())+1+'');
                    location.href='/shop/wx/lunch';
                }else{
                    alert("购买失败，请刷新页面后重试！");
                }
            })

    return true;
});
