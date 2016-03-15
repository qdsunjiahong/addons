var log = document.createElement('div');
log.setAttribute('id', 'log');
document.body.appendChild(log);

dd.config({
    agentId: $("input[name='agentId']").val(),
    corpId: $("input[name='corpId']").val(),
    timeStamp: $("input[name='timeStamp']").val(),
    nonceStr: $("input[name='nonceStr']").val(),
    signature: $("input[name='signature']").val(),
    jsApiList: ['device.notification.alert', 'device.notification.confirm']
});


dd.ready(function () {

    dd.runtime.info({
        onSuccess: function (info) {
        },
        onFail: function (err) {
            alert('fail: ' + JSON.stringify(err));
        }
    });

    dd.runtime.permission.requestAuthCode({
        corpId: $("input[name='corpId']").val(),
        onSuccess: function (info) {
            $.ajax({
                url: '/qdoo/dd/work_details?code=' + info.code + '&amp;access_token=' + $("input[name='access_token']").val(),
                type: 'GET',
                success: function (info) {
                    var res = eval("(" + info + ")");
                    if (res.key == '1') {
                        location.href = res.info;
                    }
                    else {
                        alert('auth error: ' + res.info);
                    }
                },
                error: function (xhr, errorType, error) {
                    alert(errorType + ', ' + error);
                }
            });
        },
        onFail: function (err) {
            alert('requestAuthCode fail: ' + JSON.stringify(err));
        }
    });
});

dd.error(function (err) {
    alert('dd error: ' + JSON.stringify(err));
});