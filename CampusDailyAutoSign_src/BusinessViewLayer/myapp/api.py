# __all__ = ['hnu', 'verify_input_email', 'verify_input_account']

import csv
import re
from uuid import uuid4

from email_validator import validate_email, EmailNotValidError

from BusinessCentralLayer.sentinel.noticer import send_email
from BusinessLogicLayer.cluster.slavers.hainanu import HainanUniversity
from config import SERVER_PATH_CONFIG_USER

hnu = HainanUniversity()


# 验证今日校园账号正确
def apis_account_verify(user: dict):
    """

    :param user: username password
    :return:
    """
    response = {'msg': 'failed', 'info': ''}

    if not (user.get('username') and user.get('password')):
        response.update({'info': 'Request parameter is empty'})
        return response

    hnu.user_info = user
    try:
        session = hnu.fork_api(user, hnu.apis, max_retry_num=10, delay=0.5)
        if session:
            response.update({'msg': 'success', 'info': 'Verified successfully'})
            params = hnu.get_unsigned_tasks(session)
            if params:
                task = hnu.get_detail_task(session, params)
                hnu.private_extract(task)
        else:
            response.update({'info': 'Incorrect username or password'})
    finally:
        return response


# 验证邮箱合法
def apis_email_passable(email: str) -> bool:
    """
    验证邮箱合法条件：
    1.正则合法
    2.非临时邮箱
    3.邮箱存在且通过验证
    :param email:
    :return:
    """
    # 第一层过滤：正则合法
    response = re.search("^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$", email)
    if response:
        # 第二层过滤，协议合规
        try:
            valid = validate_email(email)
            return True
        except EmailNotValidError:
            return False
    else:
        return False


def apis_account_exist(user: dict):
    username = user.get('username')
    response = {'username': username}
    try:
        if isinstance(username, str):
            with open(SERVER_PATH_CONFIG_USER, 'r', encoding='utf8') as f:
                data = [i for i in csv.reader(f) if i]
            ids = [i[1] for i in data[1:]]
            if username in ids:
                response.update({'msg': 'failed', 'info': '账号已登记'})
            else:
                response.update({'msg': 'success', 'info': '账号可登记'})
        else:
            response.update({'msg': 'failed', 'info': 'post 信息为空'})
    finally:
        return response


def apis_send_code(user: dict, verify_code_token: dict):
    response = {'msg': "", "info": ""}

    token = user.get('token')

    email = user.get('email')

    if not (token and email):
        response.update({'msg': 'failed', 'info': "参数缺失"})
        return response

    try:
        if isinstance(token, str) and isinstance(email, str):
            token_email: str or bool = verify_code_token.get(token).get('email')
            if isinstance(token_email, str) and token_email == email:
                sid = str(uuid4()).split('-')[1]
                verify_code_token[token].update({'sid': sid})
                send_email(msg=sid, to=email)
                response.update({'msg': 'success', 'info': '验证码已发送'})
            else:
                response.update({'msg': 'failed', 'info': 'token验证失败'})
        else:
            response.update({'msg': 'failed', 'info': '请求参数有误'})
    finally:
        return response


def apis_add_user(user: dict, verify_code_token: dict):
    response = {'msg': "failed", "info": ""}

    school = user.get('school')
    username = user.get('username')
    password = user.get('password')
    email = user.get('email')
    sid_usr = user.get('sid')
    token_usr = user.get('token')

    if not (token_usr and sid_usr and school and username and password and email):
        response.update({'msg': 'failed', 'info': "参数缺失"})
        return response

    try:
        if isinstance(token_usr, str) and isinstance(email, str):
            sid: str or bool = verify_code_token.get(token_usr).get('sid')
            if isinstance(sid, str) and sid == sid_usr:
                try:
                    with open(SERVER_PATH_CONFIG_USER, 'a', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([school, username, password, email])
                    response.update({'msg': 'success', 'info': '账号入库成功！'})
                except Exception as e:
                    print(e)
                    response.update({'info': '服务器接口异常'})
            else:
                response.update({'info': '验证码输入错误'})
        else:
            response.update({'info': '参数数据类型错误'})
    finally:
        return response
