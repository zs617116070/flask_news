function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $(".pic_info").submit(function (e) {
        e.preventDefault();

        /*
        $.ajax({});
        这个ajax请求一般是向服务器发送纯文本的json数据
        */

        /*
        $(this).ajaxSubmit({}); 使用表单中的ajax提交的方式
        这个ajax请求一般是向服务器发送即有文本又有文件的数据
        注意：不需要自己去读取form表单中的数据，这个ajax会自动的读取并发送，类似正真的form表单的提交一样的
        */

        //TODO 上传头像
        $(this).ajaxSubmit({
            url: "/user/pic_info",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    $(".now_user_pic").attr("src", resp.data.avatar_url);
                    $(".user_center_pic>img", parent.document).attr("src", resp.data.avatar_url)
                    $(".user_login>img", parent.document).attr("src", resp.data.avatar_url)
                }else {
                    alert(resp.errmsg)
                }
            }
        });
    });
});