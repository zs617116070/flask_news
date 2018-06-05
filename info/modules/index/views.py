# 主页的逻辑
from . import index_blue
from flask import render_template,current_app,session,request,jsonify
from info.models import User,News,Category
from info import constants,response_code


# http://127.0.0.1:5000/news_list?cid=2&page=3&per_page=10
@index_blue.route('/news_list')
def index_news_list():
    """提供主页新闻列表数据
    1.接受参数（新闻分类id,当前第几页，每页多少条）
    2.校验参数（判断以上参数是否是数字）
    3.根据参数查询用户需要的数据:根据新闻发布时间倒叙，最后时限分页
    4.构造响应的新闻数据
    5.响应新闻数据
    """
    # 1.接受参数（新闻分类id,当前第几页，每页多少条）
    cid = request.args.get('cid', '1')
    page = request.args.get('page', '1')
    per_page = request.args.get('per_page', '10')

    # 2.校验参数（判断以上参数是否是数字）
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.PWDERR, errmsg='参数有误')

    # 3.根据参数查询用户需要的数据:根据新闻发布时间倒叙，最后时限分页
    # paginate = [News,News,News,News,News,News,News,News,News,News]
    if cid == 1:
        # 当传入的新闻分类就是1，说明需要查询所有分类的新闻，按照时间倒叙，分页
        paginate = News.query.order_by(News.create_time.desc()).paginate(page, per_page, False)
    else:
        # 当传入的新闻分类不为1，说明需要查询指定分类的新闻，按照时间倒叙，分页
        paginate = News.query.filter(News.category_id==cid).order_by(News.create_time.desc()).paginate(page, per_page, False)

    # 4.构造响应的新闻数据
    # 4.1 获取paginate中的模型对象
    # news_list = [News,News,News,News,News,News,News,News,News,News]
    news_list = paginate.items
    # 4.2 获取总页数：为了实现上拉刷新
    total_page = paginate.pages
    # 4.3 当前在第几页
    current_page = paginate.page

    # 因为json在序列化时，只认得字典或者列表，不认识模型对象列表
    # 所以需要将模型对象列表转成字典列表
    # news_dict_List = [{"id":"1","nick_name":"zxc"},{{"id":"2","nick_name":"zxj"}},...]
    news_dict_List = []
    for news in news_list:
        news_dict_List.append(news.to_basic_dict())

    # 构造响应json数据的字典
    data = {
        'news_dict_List':news_dict_List,
        'total_page':total_page,
        'current_page':current_page
    }

    # 5.响应新闻数据
    return jsonify(errno=response_code.RET.OK, errmsg='OK', data=data)


@index_blue.route('/')
def index():
    """主页
    1.浏览器右上角用户信息：如果未登录主页右上角显示'登录、注册'；反之，显示'用户名 退出'
    2.主页点击排行
    3.查询和展示新闻分类标签
    """
    # 1.浏览器右上角用户信息
    # 1.1 判断用户是否登录，直接从session中取出user_id
    user_id = session.get('user_id',None)
    user = None
    if user_id:
        # 如果有user_id，说明登录中，就取出User模型对象信息
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    # 2.主页点击排行：查询新闻数据，根据clicks点击量属性实现倒叙
    # news_clicks = [News,News,News,News,News,News]
    news_clicks = []
    try:
        news_clicks = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    # 3.查询和展示新闻分类标签
    # categories == [Category,Category,Category,Category,Category,Category]
    categories = []
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    # categories_dict_list = []
    # for category in categories:
    #     categories_dict_list.append(category.to_dict())

    # 构造模板上下文
    context = {
        'user':user.to_dict() if user else None,
        'news_clicks':news_clicks,
        'categories':categories
    }

    # 渲染主页页面
    return render_template('news/index.html', context=context)


@index_blue.route('/favicon.ico', methods = ['GET'])
def favicon():
    """title左侧的图标"""
    # return '/Users/Desktop/Information_28/info/static/news/favicon.ico'
    return current_app.send_static_file('news/favicon.ico')