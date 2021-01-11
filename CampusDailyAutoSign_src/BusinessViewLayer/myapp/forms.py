from flask import Flask, request, jsonify, redirect

from BusinessViewLayer.myapp.api import *
from config import *

app = Flask(__name__)

# {email:token}
sys_token_dict = dict()
response_ = {'msg': 'failed', 'info': ''}


@app.route(ROUTE_API['my_blog'], methods=['GET'])
def my_blog():
    return redirect('https://www.qinse.top')


@app.route(ROUTE_API['tos'], methods=['GET'])
def __tos__():
    tos = '1.本项目仅为海南大学[海甸校区]提供服务；\n\n' \
          '2.本项目由海南大学机器人与人工智能协会数据挖掘小组(A-RAI.DM)负责维护；\n\n' \
          '3.禁止任何人使用本项目及其分支提供任何形式的收费代理服务；\n\n'
    title = 'CampusDailyAutoSign[For.HainanUniversity]_v1.0'
    response = {'tos': tos, 'title': title}
    return jsonify(response)


"""======================================================================"""


@app.route(ROUTE_API['verity_account_exist'], methods=['POST'])
def account_exist():
    return jsonify(apis_account_exist(request.form))


@app.route(ROUTE_API['verity_cpdaily_account'], methods=['POST'])
def account_verity():
    return jsonify(apis_account_verify(request.form))


@app.route(ROUTE_API['verity_email_passable'], methods=['POST'])
def email_passable():
    response = response_
    form: dict = request.form
    email = form.get('email')
    if email is None:
        response.update({'msg': 'failed', 'info': '数据为空'})
        return jsonify(response)
    else:
        response.update({'email': email})

    try:
        if isinstance(email, str):
            if apis_email_passable(email):
                temp_token = str(uuid4())
                response.update({'msg': 'success', 'info': '邮箱合法', 'token': temp_token})
                sys_token_dict.update({temp_token: {'email': email}})
            else:
                response.update({'msg': 'failed', 'info': '邮箱不合规', })
        else:
            response.update({'msg': 'empty', 'info': '参数不合法', })
    finally:
        return jsonify(response)


@app.route(ROUTE_API['send_verity_code'], methods=['POST'])
def send_verify_code():
    return jsonify(apis_send_code(request.form, sys_token_dict))


@app.route(ROUTE_API['add_user'], methods=['POST'])
def add_usr():
    return jsonify(apis_add_user(request.form, sys_token_dict))


"""======================================================================"""


@app.route(ROUTE_API['quick_start'], methods=['POST'])
def quick_start():
    from BusinessCentralLayer.sentinel.noticer import send_email
    form = dict(request.form)  # 解析请求
    user = dict(zip(list(form.keys()), [i[0] for i in form.values()]))

    school = form.get('school')[0]  # 学校
    username = form.get('username')[0]  # 用户名
    password = form.get('password')[0]  # 密码
    email = form.get('email')[0]  # 邮箱

    user_token = form.get('token')[0] if form.get('token') else None
    print(user_token)
    sentinel = sys_token_dict.get(user_token)

    token = str(uuid4())
    response = dict()

    try:
        if isinstance(user_token, str):
            if user_token != '':
                print('user_token:{}'.format(user_token))
                if isinstance(sentinel, dict):
                    with open(SERVER_PATH_CONFIG_USER, 'a', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([school, username, password, email])
                        response.update({'msg': 'success', 'info': '注册成功', 'args': sentinel})
        else:
            with open(SERVER_PATH_CONFIG_USER, 'r', encoding='utf8') as f:
                data = [i for i in csv.reader(f) if i]
            if all(user.values()):
                ids = [i[1] for i in data[1:]]
                if username not in ids:
                    hnu.user_info = user
                    # apis = hnu.get_campus_daily_apis(user)
                    session = hnu.get_session(user, hnu.apis, max_retry_num=10, delay=1)
                    if session:
                        res = apis_email_passable(email)
                        if res:
                            send_email(msg=token, to=email, headers='【今日校园】VerifyToken')
                            sys_token_dict.update(
                                {token: user}
                            )
                            logger.info(sys_token_dict)
                            response.update({'msg': 'success', 'info': '验证成功'})
                        else:
                            response.update({'msg': 'failed', 'info': '邮箱不合法'})
                    else:
                        response.update({'msg': 'failed', 'info': '账号或密码错误'})
                else:
                    response.update({'msg': 'failed', 'info': '账号已验证'})
            else:
                response.update({'msg': 'failed', 'info': '请求参数有误'})
    except Exception as e:
        logger.debug(e)
    finally:
        logger.success(f"{response}")
        return jsonify(response)


"""======================================================================"""

# 接收YEA的请求
YEA_API = {
    'sign_up': '/cpds/api/sign_up',
    'stu_act': '/cpds/api/stu_act',
    'stu_snp': '/cpds/api/stu_snp',
    'stu_twqd': '/cpds/api/stu_twqd',
    'stu_twqd2': '/cpds/api/stu_twqd2'  # 截图上传
}


@app.route(YEA_API['sign_up'], methods=['POST'])
def yea_sign_up():
    """
    调用业务，完成打卡任务，生成截图（基于selenium）
    :return:
    """
    pass


@app.route(YEA_API['stu_act'], methods=['POST'])
def yea_stu_act():
    """
    查询用户表,用户是否在库
    :return:
    """
    # response.update({'msg': 'failed', 'info': '账号已登记'})
    if apis_account_exist(request.form).get('info') == '账号已登记':
        return jsonify({'msg': 'success', 'info': '验证成功，用户在库'})
    else:
        return jsonify({'msg': 'failed', 'info': '验证失败，该用户没有调用权限'})


@app.route(YEA_API['stu_snp'], methods=['POST'])
def yea_stu_snp():
    """
    查询任务表，用户是否已签到
    :return:
    """
    if apis_snp_exist(request.form).get('info') == '用户已手动签到':
        return jsonify({'msg': 'success', 'info': '用户已手动签到'})
    else:
        return jsonify({'msg': 'goto', 'info': '任务待执行'})


@app.route(YEA_API['stu_twqd'], methods=['POST'])
def yea_quick_twqd():
    resp = apis_stu_twqd(request.form)
    return jsonify(resp)


# @app.route(YEA_API['reload_cookie'], methods=['POST'])
def yea_reload_superuser_cookie():
    resp = apis_reload_superuser_cookie()
    return jsonify(resp)


@app.route(YEA_API['stu_twqd2'], methods=['POST'])
def yea_quick_twqd_plus():
    """
    当OSS没有截图时使用此接口
    既已知OSS没有截图，故无论osh-slaver如何执行，都要调用 osh-s上传截图
    :return:
    """
    resp = apis_stu_twqd_plus(request.form)
    return jsonify(resp)


"""======================================================================"""
if __name__ == '__main__':
    app.run(port=6600, host='0.0.0.0', debug=True)
