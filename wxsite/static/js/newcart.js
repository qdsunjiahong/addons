/**
 * Created by wh on 16-3-18.
 */
//数量调整
$('.change-quantity').each(function(){
    var cartID = $(this).attr('id');

    $(this).find('a').click(function(){
        var qtyInput = $(this).parent().find('.buy-quantity'),  //购买数量
            quantity = parseFloat(qtyInput.val());  //当前购买数量

        if($(this).hasClass('quantity-add')){
            quantity += 1;
        }else if($(this).hasClass('quantity-reduce')){
            quantity -= 1;
        }

        if(quantity<0){
            alert('数量不能小于0哦～');
            return true;
        }

        $.ajax({
            url: '/shop/wx/onchange',
            type: 'POST',
            data: {
                action: 'update',
                cartid: cartID,
                number: quantity,
            },
            dataType: 'json',
            success: function(msg){
                if(msg.key == 1){
                    $('b.cart-num').text(msg.all_car_num+'');
                    $('b.cart-sum').text(msg.all_money+'');
                    $('.pay-sum b').text(msg.all_money+'');
                    qtyInput.val(quantity);
                }else{
                    alert("操作失败！");
                }
            }
        });


    });
});


//页面加载后计算份数
var allQuantity = 0;
$('input.buy-quantity').each(function(){
    var thisQuantity = parseFloat($(this).val());
    allQuantity += thisQuantity;
});
allQuantity = parseFloat(Math.round(allQuantity*100)/100);
$('.cart-num').text(allQuantity+'');


//点击确认按钮，提交表单
$('button[name="suborder"]').click(function(){
    //可以在此做一些检验

    $('form#subform').submit();
});

