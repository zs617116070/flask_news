# 注册和登录
from . import passport_blue
from flask import request,abort,current_app,make_response,jsonify,session,json
from info.utils.captcha.captcha import captcha
from info import redis_store, constants,response_code,db
import json,re,random,datetime
from info.libs.yuntongxun.sms import CCP
from info.models import User


@passport_blue.route('/logout', methods=['GET'])
def logout():
    """退出登录"""
    # 1.清理session数据
    try:
        session.pop('user_id',None)
        session.pop('mobile',None)
        session.pop('nick_name',None)

        # 为了防止管理员误入前台，留下is_admin状态保持信息，所以不管谁在退出登录，都要把is_admin清理
        session.pop('is_admin', False)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='退出登录失败')

    return jsonify(errno=response_code.RET.OK, errmsg='退出登录成功')


@passport_blue.route('/login', methods=['POST'])
def login():
    """登录
    1.接受参数（手机号，密码明文）
    2.校验参数（判断参数是否齐全，手机号是否合法）
    3.使用手机号查询用户信息
    4.匹配该要登录的用户的密码
    5.更新最后一次登录的时间
    6.将状态保持数据写入到session
    7.响应登录结果
    """
    # 1.接受参数（手机号，密码明文）
    json_dict = request.json
    mobile = json_dict.get('mobile')
    password = json_dict.get('password')

    # 2.校验参数（判断参数是否齐全，手机号是否合法）
    if not all([mobile,password]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
    if not re.match(r'^1[345678][0-9]{9}$', mobile):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='手机号格式错误')

    # 3.使用手机号查询用户信息
    try:
        user = User.query.filter(User.mobile==mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询用户数据失败')
    if not user:
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='用户名或密码错误')

    # 4.匹配该要登录的用户的密码
    if not user.check_password(password):
        return jsonify(errno=response_code.RET.PWDERR, errmsg='用户名或密码错误')

    # 5.更新最后一次登录的时间
    user.last_login = datetime.datetime.now()
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=response_code.RET.DBERR, errmsg='更新最后一次登录的时间失败')

    # 6.将状态保持数据写入到session
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name

    # 7.响应登录结果
    return jsonify(errno=response_code.RET.OK, errmsg='登录成功')


@passport_blue.route('/register', methods=['POST'])
def register():
    """注册
    1.接受参数（手机号，短信验证码，密码明文）
    2.校验参数（判断参数是否齐全，手机号是否合法）
    3.查询服务器存储的短信验证码
    4.跟客户端传入的短信验证码对比
    5.如果对比成功，创建User模型对象，并赋值属性
    6.同步模型对象到数据库
    7.将状态保持数据写入到session（实现注册即登录）
    8.响应注册结果
    """
    # 1.接受参数（手机号，短信验证码，密码明文）
    # request.json == json.loads(request.data)
    json_dict = request.json
    mobile = json_dict.get('mobile')
    smscode_client = json_dict.get('smscode')
    password = json_dict.get('password')

    # 2.校验参数（判断参数是否齐全，手机号是否合法）
    if not all([mobile, smscode_client, password]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
    if not re.match(r'^1[345678][0-9]{9}$', mobile):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='手机号格式错误')

    # 3.查询服务器存储的短信验证码
    try:
        smscode_server = redis_store.get('SMS:'+mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询短信验证码失败')
    if not smscode_server:
        return jsonify(errno=response_code.RET.NODATA, errmsg='短信验证码不存在')

    # 4.跟客户端传入的短信验证码对比
    if smscode_server != smscode_client:
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='输入短信验证码有误')

    # 5.如果对比成功，创建User模型对象，并赋值属性
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    # 密码需要加密在存储的
    # 在当前视图中，对password加密，在赋值给password_hash
    # 封装一个加密的方法，在当前视图中调用，对password加密，在赋值给password_hash
    # 我选择的:在models.py中的User模型类中封装一个属性的setter和getter方法，完成密码的加密后赋值
    # psd = user.password # getter
    user.password = password # setter
    # 注册即登录，所以记录最后一次登录的时间
    user.last_login = datetime.datetime.now()

    # 6.同步模型对象到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=response_code.RET.DBERR, errmsg='存储注册数据失败')

    # 7.将状态保持数据写入到session（实现注册即登录）
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name

    # 8.响应注册结果
    return jsonify(errno=response_code.RET.OK, errmsg='注册成功')


@passport_blue.route(r'/sms_code', methods=['POST'])
def sms_code():
    """发送短信验证码
    1.接受参数（手机号，图片验证码，图片验证码编号）
    2.校验参数（判断参数是否存在，手机号是否合法）
    3.查询服务器存储的图片验证码
    4.跟客户端传入的图片验证码对比
    5.如果对比成功，生成短信验证码数字
    6.调用CCP()单例类封装的发送短信的方法，发送短信
    7.将短信验证码存储到服务器(将来注册时要判断短信验证码是否正确)
    8.响应发送短信验证码的结果
    """
    # 1.接受参数（手机号，图片验证码，图片验证码编号）
    # '{'mobile':'17600992168','image_code':1234,'image_code_id':'uuid'}'
    json_str = request.data
    json_dict = json.loads(json_str)
    mobile = json_dict.get('mobile')
    image_code_clinet = json_dict.get('image_code')
    image_code_id = json_dict.get('image_code_id')

    # 2.校验参数（判断参数是否存在，手机号是否合法）
    if not all([mobile,image_code_clinet,image_code_id]):
        # '{'errno':'0', 'errmsg':'OK'}'
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
    if not re.match(r'^1[345678][0-9]{9}$', mobile):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='手机号格式错误')

    # 3.查询服务器存储的图片验证码
    try:
        image_code_server = redis_store.get('ImageCode:'+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询图片验证码失败')
    if not image_code_server:
        return jsonify(errno=response_code.RET.NODATA, errmsg='图片验证码不存在')

    # 4.跟客户端传入的图片验证码对比
    if image_code_server.lower() != image_code_clinet.lower():
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='输入验证码有误')

    # 5.如果对比成功，生成短信验证码数字
    # '%06d' : 不够6位补0；比如，34--》000034
    sms_code = '%06d' % random.randint(0, 999999)
    current_app.logger.debug(sms_code)

    # 6.调用CCP()单例类封装的发送短信的方法，发送短信
    # result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    # if result != 0:
    #     return jsonify(errno=response_code.RET.THIRDERR, errmsg='发送短信验证码失败')

    # 7.将短信验证码存储到服务器(将来注册时要判断短信验证码是否正确)
    try:
        redis_store.set('SMS:'+mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='存储短信验证码失败')

    #  8.响应发送短信验证码的结果
    return jsonify(errno=response_code.RET.OK, errmsg='发送短信验证码成功')


@passport_blue.route('/image_code')
def image_code():
    """提供图片验证码
    1.接受参数（图片验证码唯一标识uuid）
    2.校验参数（判断参数是否存在）
    3.生成图片验证码
    4.存储图片验证码
    5.将图片的类型指定为image/jpg
    6.响应图片验证码
    """
    # 1.接受参数（图片验证码唯一标识uuid）
    imageCodeId = request.args.get('imageCodeId')

    # 2.校验参数（判断参数是否存在）
    if not imageCodeId:
        abort(403)

    # 3.生成图片验证码:text写入到redis,image响应到浏览器
    name,text,image = captcha.generate_captcha()
    current_app.logger.debug(text)

    # 4.存储图片验证码
    try:
        redis_store.set('ImageCode:'+imageCodeId, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)

    # 5.将图片的类型指定为image/jpg
    response = make_response(image)
    # 设置响应头信息
    response.headers['Content-Type'] = 'image/jpg'

    # 6.响应图片验证码
    return response