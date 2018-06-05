var currentCid = 1; // 当前分类 id
var cur_page = 1; // 当前页
var total_page = 1;  // 总页数
var data_querying = true;   // 是否正在向后台获取数据。为true时不能上拉刷新。反之，可以上拉刷新


$(function () {
    // 当主页加载完成后，立即主动的获取新闻列表数据
    updateNewsData();

    // 首页分类切换
    $('.menu li').click(function () {
        var clickCid = $(this).attr('data-cid');
        $('.menu li').each(function () {
            $(this).removeClass('active')
        });
        $(this).addClass('active');

        if (clickCid != currentCid) {
            // 记录当前分类id
            currentCid = clickCid;

            // 重置分页参数:默认还是从第一页加载
            cur_page = 1;
            total_page = 1;
            updateNewsData()
        }
    });

    //页面滚动加载相关
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        if ((canScrollHeight - nowScroll) < 100) {
            // TODO 判断页数，去更新新闻数据
            if (!data_querying) {
                // 加载下一页数据
                data_querying = true; // 表示正在加载数据

                // total_page = 116
                // 课堂的代码，有问题的 114
                // cur_page += 1;

                // 判断是否是最后一页，如果不是最后一页可以继续加载下一页
                if (cur_page < total_page) {

                    // 第二天的反馈修改：先判断再进入累加当前页
                    cur_page += 1;

                    updateNewsData()
                }
            }
        }
    })
})

function updateNewsData() {
    // TODO 更新新闻数据
    var params = {
        'cid':currentCid,
        'page':cur_page
        // 不需要传入per_page,因为默认10
    };

    $.get('/news_list', params, function (response) {
        // 能够执行到这里说明数据加载完成，有可能失败，有可能成功
        data_querying = false; // 表示没有正在加载数据,可以上拉

        if (response.errno == '0') {
            // 在响应成功后，需要记录分页之后的总页数（服务器告诉前端一共多少页）
            total_page = response.data.total_page;

            // 清空第一页数据:为了不让前一个分类的第一页数据追加到下一个分类中
            if (cur_page == 1) {
                $(".list_con").html("");
            }

            // 获取数据成功，使用新的数据渲染界面
            for (var i=0;i<response.data.news_dict_List.length;i++) {
                var news = response.data.news_dict_List[i]
                var content = '<li>'
                content += '<a href="/news/detail/'+news.id+'" class="news_pic fl"><img src="' + news.index_image_url + '?imageView2/1/w/170/h/170"></a>'
                content += '<a href="/news/detail/'+news.id+'" class="news_title fl">' + news.title + '</a>'
                content += '<a href="/news/detail/'+news.id+'" class="news_detail fl">' + news.digest + '</a>'
                content += '<div class="author_info fl">'
                content += '<div class="source fl">来源：' + news.source + '</div>'
                content += '<div class="time fl">' + news.create_time + '</div>'
                content += '</div>'
                content += '</li>'
                // append表示将新的数据追加到旧的数据的后面；html表示将新的数据替换到旧的数据的后面；
                $(".list_con").append(content)
            }
        } else {
            alert(response.errmsg);
        }
    });
}
