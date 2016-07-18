/*
//重设顶部菜单内容宽度
var catsLength = $('.top-cats ul:first li').length*4;
$('.top-cats ul:first').css('width', catsLength+'em');

//顶部菜单拖拽
var dragX = 0;
$('.top-cats ul:first').drag({
    process: function(e){
        var pageX = e.pageX;
        
        if(dragX == 0)dragX = pageX;
        
        var moveX = parseInt(pageX - dragX);
        if(moveX > 0)moveX = 0;
        
        
        $('.top-cats ul:first').css({
            'left': moveX+'px',
            'top': '0'
        });
    },
    end: function(e){
//        var pageX = e.pageX;
//        
//        if(dragX != pageX)dragX = pageX;
    }
});
*/

//更改购买数量
$('.select-product a').click(function(){
	var pid = $(this).parent().prop('id'),
		quantity = parseFloat($(this).parent().find('span').text());

	if($(this).hasClass('quantity-reduce')){
		quantity -= 1;
	}else if($(this).hasClass('quantity-add')){
		quantity += 1;
	}

	if(quantity >= 0){
		$.ajax({
			url: '/shop/wx/onchange',
			type: 'POST',
			data: {
				action: 'update',
				cartid: pid,
				number: quantity,
			}
		}).done(function(msg){
			if(msg == '1'){
				location.href='/shop/wx/lunch';
			}else{
				alert('操作失败，请刷新页面！');
			}
		});
	}else{
		alert('购买数量不合法!');
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
