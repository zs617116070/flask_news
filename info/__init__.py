from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from config import Config, DevelopmentConfig, ProductionConfig, UnittestConfig
from config import configs
import logging
from logging.handlers import RotatingFileHandler
from flask_wtf import csrf


def setup_log(level):

    # 设置日志的记录等级
    logging.basicConfig(level=level)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
    # 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 创建SQLAlchemy对象
db = SQLAlchemy()
redis_store = None


def create_app(config_name):
    """根据参数的参数，创建app
    参数：就是外界传入的配置环境
    """

    # 集成日志：根据不同的配置环境，加载不同的日志等级
    # setup_log(DevlopementConfig)
    setup_log(configs[config_name].LEVEL_LOG)

    app = Flask(__name__)

    # 配置文件的加载
    app.config.from_object(configs[config_name])

    # 创建连接到MySQL数据库的对象
    # db = SQLAlchemy(app)
    db.init_app(app)

    # 创建连接到Redis数据库的对象
    global redis_store
    redis_store = StrictRedis(host=configs[config_name].REDIS_HOST, port=configs[config_name].REDIS_PORT, decode_responses=True)

    # 开启CSRF保护:提示，当我们不使用flask_wtf扩展中的Flask_Form类自定义表单时，需要自己开启CSRF保护
    CSRFProtect(app)

    # 业务一开始，就准备请求勾子，在每次的请求结束后向浏览器写入cookie
    @app.after_request
    def after_request(response):
        # 1.生成csrf_token值
        csrf_token = csrf.generate_csrf()
        # 2.将csrf_token值写入到浏览器
        response.set_cookie('csrf_token',csrf_token)
        return response

    # 将自定义的过滤器函数，转成模板中可以直接使用的过滤器
    from info.utils.comment import do_rank
    app.add_template_filter(do_rank, 'rank')

    # 配置flask_session,将session数据写入到服务器的redis数据库
    Session(app)

    # 将蓝图注册到app：
    # 注意点：蓝图在哪里注册就在哪里导入，避免在当如蓝图时某些变量还没有加载出来
    from info.modules.index import index_blue
    app.register_blueprint(index_blue)
    from info.modules.passport import passport_blue
    app.register_blueprint(passport_blue)
    from info.modules.news import news_blue
    app.register_blueprint(news_blue)
    from info.modules.user import user_blue
    app.register_blueprint(user_blue)

    from info.modules.admin import admin_blue
    app.register_blueprint(admin_blue)

    # 一定要记得返回app
    return app