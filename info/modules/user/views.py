# 个人中心模块
from . import user_blue
from flask import render_template,g,redirect,url_for,request,jsonify,current_app,session
from info.utils.comment import user_login_data
from info import response_code,db,constants
from info.utils.file_storage import upload_file
from info.models import News,Category



@user_blue.route('/news_list')
@user_login_data
def user_news_list():
    """用户发布的新闻列表"""

    # 1.获取登录用户信息：没有渲染界面，不需要to_dict()
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 2.获取参数
    page = request.args.get('p', '1')

    # 3.校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = '1'

    # 4.查询登录用户发布的新闻,并且进行分页
    paginate = None
    try:
        paginate = News.query.filter(News.user_id==user.id).paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
    except Exception as e:
        current_app.logger.error(e)

    # 5.构造响应数据
    news_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    context = {
        'news_list':news_dict_list,
        'total_page':total_page,
        'current_page':current_page
    }

    # 6.渲染
    return render_template('news/user_news_list.html',context=context)


@user_blue.route('/news_release', methods=['GET','POST'])
@user_login_data
def news_release():
    """新闻发布"""

    # 1.获取登录用户信息：没有渲染界面，不需要to_dict()
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 2.GET请求逻辑：渲染发布新闻的界面
    if request.method == 'GET':
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)

        # 不需要显示"最新"
        categories.pop(0)

        context = {
            'categories':categories
        }

        return render_template('news/user_news_release.html',context=context)

    # 3.POST请求逻辑：实现新闻发布后端的逻辑
    if request.method == 'POST':
        # 3.1 接受参数
        title = request.form.get("title")
        source = "个人发布"
        digest = request.form.get("digest")
        content = request.form.get("content")
        index_image = request.files.get("index_image")
        category_id = request.form.get("category_id")

        # 3.2 校验参数
        if not all([title,source,digest,content,index_image,category_id]):
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')

        # 校验和读取用户上传的图片二进制，需要转存到七牛
        try:
            index_image_data = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='读取图片失败')

        # 将用户头像存储到七牛
        try:
            key = upload_file(index_image_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.THIRDERR, errmsg='上传图片失败')

        # 3.3 新建新闻模型对象，并赋值和同步到数据库
        news = News()
        news.title = title
        news.digest = digest
        news.source = source
        news.content = content
        # 这里需要拼接前缀是迫不得已，因为一般的新闻的网站的数据都是从其他地方爬虫过来的,那个时候需要将爬过来的url全局保存
        # 如果我在models中to_dict()中加七牛的前缀，会造成 七牛前缀+新闻图片url
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        news.category_id = category_id
        news.user_id = user.id
        # 1代表待审核状态
        news.status = 1

        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.DBERR, errmsg='保存发布的新闻失败')

        # 3.4 响应新闻发布的结果
        return jsonify(errno=response_code.RET.OK, errmsg='发布新闻成功')


@user_blue.route('/user_collection')
@user_login_data
def user_collection():
    """用户收藏"""

    # 1.获取登录用户信息：没有渲染界面，不需要to_dict()
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 2.接受参数：如果没有值默认是第一页
    page = request.args.get('p', '1')

    # 3.校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        # 如果瞎传，默认也给1
        page = '1'

    # 3.分页查询
    paginate = None
    try:
        paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
    except Exception as e:
        current_app.logger.error(e)

    # 4.构造响应数据
    news_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    context = {
        'news_list':news_dict_list,
        'total_page':total_page,
        'current_page':current_page
    }

    # 5.响应结果
    return render_template('news/user_collection.html', context=context)


@user_blue.route('/pass_info', methods=['GET','POST'])
@user_login_data
def pass_info():
    """修改密码"""

    # 1.获取登录用户信息：没有渲染界面，不需要to_dict()
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 2.渲染修改密码界面
    if request.method == 'GET':
        return render_template('news/user_pass_info.html')

    # 3.修改密码逻辑实现
    if request.method == 'POST':
        # 3.1 接受参数（原密码个新密码）
        old_password = request.json.get('old_password')
        new_password = request.json.get('new_password')

        # 3.2 校验密码
        if not all([old_password, new_password]):
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')

        # 3.3 判断原密码是否正确：修改密码时旧的密码必须是当前登录用户的密码（不能让别人随便输入123就能修改我的密码）
        if not user.check_password(old_password):
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='原密码输入有误')

        # 3.4 将新密码重新赋值给模型对象
        # password : 是在注册时封装的setter方法
        user.password = new_password

        # 3.5 同步到数据库
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.DBERR, errmsg='修改密码失败')

        # 3.6 响应修改密码结果
        return jsonify(errno=response_code.RET.OK, errmsg='修改密码成功')


@user_blue.route('/pic_info', methods=['GET','POST'])
@user_login_data
def pic_info():
    """设置头像
    """
    # 1.获取登录用户信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 2.GET请求逻辑
    if request.method == 'GET':
        # 2.1 构造渲染界面的数据
        context = {
            'user': user.to_dict()
        }

        # 2.2 渲染界面
        return render_template('news/user_pic_info.html', context=context)

    # 3.POST请求逻辑
    if request.method == 'POST':
        # 上传用户头像
        # 3.1 接受上传的图片文件
        avatar_file = request.files.get('avatar')

        # 3.2 校验图片文件是否收到
        try:
            avatar_data = avatar_file.read()
        except Exception as e:
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='读取头像失败')

        # 3.3 将图片文件上传的七牛
        try:
            key = upload_file(avatar_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.THIRDERR, errmsg='上传失败')

        # 3.4 上传成功将key存储到数据库
        user.avatar_url = key
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.DBERR, errmsg='存储头像信息失败')

        # 构造响应数据：因为要实现上传图像结束后直接刷新出该头像
        data = {
            'avatar_url':constants.QINIU_DOMIN_PREFIX + key
        }

        # 3.5 响应上传头像结果
        return jsonify(errno=response_code.RET.OK, errmsg='上传头像成功',data=data)


@user_blue.route('/base_info', methods=['GET','POST'])
@user_login_data
def base_info():
    """基本资料
    """
    # 1.获取登录用户信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 2.GET请求逻辑
    if request.method == 'GET':
        # 2.1 构造渲染界面的数据
        context = {
            'user':user.to_dict()
        }

        # 2.2 渲染界面
        return render_template('news/user_base_info.html', context=context)

    # 3.POST请求逻辑
    if request.method == 'POST':
        # 3.1 接受参数（签名，昵称，性别）
        nick_name = request.json.get('nick_name')
        signature = request.json.get('signature')
        gender = request.json.get('gender')

        # 3.2 校验参数
        if not all([nick_name,signature,gender]):
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
        if gender not in ['MAN', 'WOMAN']:
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

        # 3.3 保存用户修改的数据
        user.nick_name = nick_name
        user.signature = signature
        user.gender = gender

        # 3.4 同步到数据库
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.DBERR, errmsg='修改基本资料失败')

        # 4.重新修改状态保持数据里面nick_name
        session['nick_name'] = nick_name

        # 5 响应基本资料修改结果
        return jsonify(errno=response_code.RET.OK, errmsg='修改基本资料成功')


@user_blue.route('/info')
@user_login_data
def user_info():
    """个人中心入口
    注意：用户必须登录后才能进入个人中心
    """

    # 查询登录用户的信息
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 构造渲染模板的上下文
    context = {
        'user':user.to_dict()
    }

    # 渲染个人中心入口模板
    return render_template('news/user.html', context=context)
