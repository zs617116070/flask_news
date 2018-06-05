# 后台管理
from . import admin_blue
from flask import request,render_template,current_app,session,redirect,url_for,g
from info.models import User
from info.utils.comment import user_login_data
import time,datetime


@admin_blue.route('/user_count')
def user_count():
    """用户量统计"""

    # 用户总数
    total_count = 0
    try:
        # 管理员不在统计范围内
        total_count = User.query.filter(User.is_admin==False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 月新增数
    month_count = 0
    # 计算每月开始时间 比如：2018-06-01 00：00：00
    t = time.localtime()
    # 生成当前月份开始时间字符串
    month_begin = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    # 生成当前月份开始时间对象
    month_begin_date = datetime.datetime.strptime(month_begin, '%Y-%m-%d')
    try:
        month_count = User.query.filter(User.is_admin == False,User.create_time>month_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 日新增数 : 2018-06-04 00：00：00 <= create_time < 2018-06-04 24：00：00
    day_count = 0
    # 计算当天的开始时间 比如：2018-06-04 00：00：00
    day_begin = '%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)
    day_begin_date = datetime.datetime.strptime(day_begin, '%Y-%m-%d')
    try:
        day_count = User.query.filter(User.is_admin == False,User.create_time>day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    context = {
        'total_count':total_count,
        'month_count':month_count,
        'day_count':day_count
    }

    return render_template('admin/user_count.html',context=context)


@admin_blue.route('/')
@user_login_data
def admin_index():
    """主页"""

    # 获取登录用户的信息
    user = g.user
    if not user:
        return redirect(url_for('admin.admin_login'))

    context = {
        'user':user.to_dict()
    }

    return render_template('admin/index.html', context=context)


@admin_blue.route('/login', methods=['GET','POST'])
def admin_login():
    """登录"""

    # 提供登录界面
    if request.method == 'GET':

        # 检查用户是否已经登录，如果已经登录就进入到主页
        user_id = session.get('user_id',None)
        is_admin = session.get('is_admin', False)
        if user_id and is_admin:
            return redirect(url_for('admin.admin_index'))

        return render_template('admin/login.html')

    # 实现登录逻辑
    if request.method == 'POST':
        # 接受参数
        username = request.form.get('username')
        password = request.form.get('password')

        # 校验参数
        if not all([username,password]):
            return render_template('admin/login.html',errmsg='缺少参数')

        # 查询要登录的用户是否存在
        try:
            user = User.query.filter(User.nick_name==username).first()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/login.html',errmsg='查询用户数据失败')
        if not user:
            return render_template('admin/login.html',errmsg='用户名或者密码错误')

        # 校验要登录的用户的密码是否正确
        if not user.check_password(password):
            return render_template('admin/login.html',errmsg='用户名或者密码错误')

        # 写入状态保持信息到session
        session['user_id'] = user.id
        session['nick_name'] = user.nick_name
        session['mobile'] = user.mobile
        session['is_admin'] = user.is_admin

        # 响应登录结果
        return redirect(url_for('admin.admin_index'))