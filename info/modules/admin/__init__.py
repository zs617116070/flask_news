from flask import Blueprint,session,redirect,url_for,request


# 创建主页的蓝图
admin_blue = Blueprint('admin', __name__, url_prefix='/admin')


# 导入views，保证蓝图注册路由的代码能够被执行
from . import views


@admin_blue.before_request
def check_admin():
    """每次访问站点时需要做用户身份的校验"""

    # 读取用户身份信息
    is_admin = session.get('is_admin', False)
    # 1.如果用户是不管理员，访问后台管理的主页时，进入到前台的主页
    # 2.当用户访问/admin/login的时候，无论你是什么身份，都可以进入到/admin/login
        # 2.1 所以就要求，只有当request.url不为/admin/login的时候，才进入'index.index'
    if not is_admin and not request.url.endswith('/admin/login'):
        return redirect(url_for('index.index'))