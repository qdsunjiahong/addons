//左侧菜单拖拽
var dragY = 0,  //拖拽的Y坐标
	lastDragY = 0,  //步步紧随的Y坐标
	currPositionY = 30,  //当前页面位置的Y坐标
	dragDistance = 0;  //拖拽的距离

$('.top-cats').drag({
    process: function(e){
        dragY = parseInt(e.pageY);
		if(lastDragY==0)lastDragY = dragY - 1;
		dragDistance = dragY - lastDragY;
		lastDragY = dragY;

		currPositionY += dragDistance;

		$('.top-cats').css({
			'left': '1%',
			'top': currPositionY+'px'
		});

    },
    end: function(e){
		lastDragY = 0;

		if(currPositionY > 30){
			var stepLong = parseInt((currPositionY-30)/25);
			var recoverY = setInterval(function(){
				currPositionY -= stepLong;
				$('.top-cats').css('top', currPositionY+'px');

				if(currPositionY < 31){
					clearInterval(recoverY);
				}
			},10)
		}
    }
});
//左侧菜单拖拽结束

function chQuantity(pid, addOrReduce){
    var thisDiv = $('div.select-product[id="'+pid+'"]'),
		quantity = 1;  //默认为1

    if(thisDiv.find('span').length > 0){  //如果有数量，则在此数量上进行加减
        quantity = parseInt(thisDiv.find('span').text());
        if(addOrReduce == 'add'){
		    quantity += 1;
	    }else if(addOrReduce == 'reduce'){
		    quantity -= 1;
	    }
    }

	if(quantity > 0){
		$.ajax({
			url: '/shop/wx/onchange',
			type: 'POST',
			data: {
				action: 'update',
				cartid: pid,
				number: quantity,
			}
		}).done(function(msg){  //msg是更改后该产品在购物车内数量，-1表示操作失败
			var chedQuantity = quantity;
            var res = eval("("+msg+")");
			if(res.key == '1'){
				if(thisDiv.find('span').text()=='0'){  //如果没有减号和数量，则添加
					thisDiv.append('<a href="javascript:void(0)" name="reduce" class="quantity-reduce" title="减少购买数量" onclick="chQuantity('+pid+', \'reduce\')"></a>');
				    thisDiv.find('span').text(chedQuantity+'');
                    $('.selected-quantity').find('span').text(res.all_car_num);
                    $('.selected-sum').find('span').text(res.all_money);
                }else{
                    thisDiv.find('span').text(chedQuantity+'');
                    $('.selected-quantity').find('span').text(res.all_car_num);
                    $('.selected-sum').find('span').text(res.all_money);
                }
			}else{
				alert('操作失败，请刷新页面！');
			}
		});
	}else{
		alert('购买数量不合法!');
	}
}

//将页面已有的加减号点击事件绑定到处理函数中
$('.select-product a').click(function(){
	var pid = $(this).parent().prop('id');

    if($(this).hasClass('quantity-reduce')){
        chQuantity(pid, 'reduce');
    }else if($(this).hasClass('quantity-add')){
        chQuantity(pid, 'add');
    }
});

//顶部定时滚动
setInterval(function(){
    var currIndex = 0;

    $('.index-scrolls a').each(function(){
        if($(this).find('img').hasClass('curr-img')){
            currIndex = $(this).index();
        }
    });

    var scrollNum = $('.index-scrolls img').length,
        nextIndex = currIndex + 1>scrollNum-1?0:currIndex+1;

    $('.index-scrolls img.curr-img').removeClass('curr-img');
    $('.index-scrolls a:eq('+nextIndex+')').find('img').addClass('curr-img');

    $('.scroll-marks li.curr-mark').removeClass('curr-mark');
    $('.scroll-marks li:eq('+nextIndex+')').addClass('curr-mark');


}, 3000);
