//统计金额
//function sum(){
//    //统计各项菜品小计，并进行累加输出
//    var sum = 0.00,  //累计
//        subSum = 0.00;  //小计
//
//    //遍历每个菜品，勾选的菜进行计算
//    $('.product').each(function(){  //循环商铺其下各商品
//        var checkBox = $(this).find('.check input[type="checkbox"]'),
//            cartID = checkBox.val();
//
//        //计算小计
//        subSum = parseFloat($('b#price'+cartID).text()) * parseFloat($('input[name="quantity'+cartID+'"]').val());  //小计 = 价格 x 数量
//        subSum = Math.round(subSum * 100) / 100;  //精确到小数点后两位
//        $('b#subsum'+cartID).text(subSum+'');  //刷新小计
//
//        //如果本菜品勾选，则计入总金额
//        if(checkBox.prop('checked') == true){
//            sum += subSum;
//        }
//    });
//
//    sum = Math.round(sum * 100) / 100;  //精确到小数点后2位
//
//    $('.sum').html('金额：<b>'+parseFloat(sum)+'</b>元');
//}

//点击“删除”链接删除选项项
$('a.delcart').click(function(){
    var cartID = $(this).attr('id');

    //以下是一些ajax调用示例
    $.ajax({
        url: '/shop/wx/onchange',
        type: 'POST',
        data: {
            action: 'del',
            cartid: cartID
        }}).done(function(msg){
            var res = eval("("+msg+")");
            if(res.key == '1'){  //删除成功
                location.href='/shop/wx/car';
            }else{
                alert("操作失败，请刷新页面！");
            }
        });
});

//单个项目勾选/取消勾选，都将重新计算金额
//$('.check input').click(function(){
    //sum();
//});
    
//购买数量加减
$('a.chquantity').click(function(){
    var quanInput = $(this).parent().find('input.quantity'),  //购买数量输入框
        quantity = parseFloat(quanInput.val());  //当前购买数量

    if($(this).prop('name')=='reduce'){
        quantity -= 1;
    }else if($(this).prop('name')=='add'){
        quantity += 1;
    }
    //获取产品id
    var cartID = $(this).prop('id');
    //quantity = Math.round(quantity * 100) / 100;  //精确到小数点后2位

    if(quantity>0) {  //购买数量必须大于0

        $.ajax({
            url: '/shop/wx/onchange',
            type: 'POST',
            data: {
                action: 'update',
                cartid: cartID,
                number: quantity,
            }
        }).done(function (msg) {
            var res = eval("("+msg+")");
            if (res.key == '1') {  //操作成功
                location.href = '/shop/wx/car';
            } else {
                alert("操作失败，请刷新页面！");
            }
        });
    }

        //var price  = parseFloat($(this).parent().find('.price b').text()),
        //    subSum = price * quantity;  //计算小计

        //subSum = Math.round(subSum * 100) / 100;  //精确到小数点后2位

        //quanInput.val(parseFloat(quantity)+'');  //写回小计

        //sum();  //重新计算金额
    else {
        alert("购买数量不合法！")
        }
});
    
//购买数量改变
$('input.quantity').change(function(){
    var quantity = parseFloat($(this).val());

    if(quantity<0){
        alert('购买数量错误');
    }else{
        var price  = parseFloat($(this).parent().find('.price b').text()),
            subSum = price * quantity;  //计算小计

        subSum = Math.round(subSum * 100) / 100;  //精确到小数点后2位
        //sum();
    }
});

//点击确认按钮，提交表单
$('button[name="suborder"]').click(function(){
    //可以在此做一些检验


    
    $('form#subform').submit();
});


//sum();  //页面加载后执行一次金额计算