from redis import StrictRedis
import logging


class Config(object):
    """配置文件的加载"""

    # 配置秘钥：项目中的CSRF和session需要用到，还有一些其他的签名算法也要用到
    SECRET_KEY = 'q7pBNcWPgmF6BqB6b5VICF7z7pI+90o0O4CaJsFGjzRsYiya9SEgUDytXvzFsIaR'

    # 开启调试模式
    DEBUG = True

    # 配置MySQL数据库:实际开发写数据库的真实ip
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/information_28'
    # 不追踪数据库的更改，因为会有明显的开销
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置Redis数据库:redis模块不是flask的扩展，是python的一个包而已
    # 所以这里写的格式和SQLAlchemy的配置一样，但是，app不会自动的读取，就需要自己读
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # 配置flask_session,将session数据写入到服务器的redis数据库
    # 指定session数据存储在redis
    SESSION_TYPE = 'redis'
    # 告诉session服务器redis的位置
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 是否将session签名后再存储
    SESSION_USE_SIGNER = True
    # 当SESSION_PERMANENT为True时，设置session的有效期才可以成立，正好默认就是True
    PERMANENT_SESSION_LIFETIME = 60*60*24 # 自定义为一天有效期


class DevelopmentConfig(Config):
    """开发环境下的配置：项目开发中"""
    pass # 开发环境的配置和父类基本一致，所以pass

    # 开发环境下的日志等级
    LEVEL_LOG = logging.DEBUG


class ProductionConfig(Config):
    """生产环境下的配置：项目上线后"""

    # 关闭调试模式
    DEBUG = False
    # 指定生产环境下的数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/information_pro_28'

    # 生产环境下的日志等级
    LEVEL_LOG = logging.ERROR


class UnittestConfig(Config):
    """开发环境下的配置"""

    # 开启测试模式
    TESTING = True
    # 指定测试数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/information_cast_28'
    # 测试环境下的日志等级
    LEVEL_LOG = logging.DEBUG


# 准备工厂方法create_app(参数)的原材料
configs = {
    'dev':DevelopmentConfig,
    'pro':ProductionConfig,
    'unit':UnittestConfig
}






