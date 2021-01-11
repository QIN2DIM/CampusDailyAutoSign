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


# ====================================================================

def apis_snp_exist(user: dict) -> dict:
    import os
    from config import SERVER_DIR_SCREENSHOT
    osh_day = user.get('osh_day')
    username = user.get('username')
    osh_model_day = os.path.join(SERVER_DIR_SCREENSHOT, osh_day)

    if "{}.png".format(username) in os.listdir(osh_model_day):
        return {'info': '用户已手动签到', 'msg': 'success'}
    else:
        return {'info': '用户待签到', 'msg': 'goto'}


def _select_user_table(username) -> dict or bool:
    with open(SERVER_PATH_CONFIG_USER, 'r', encoding='utf8') as f:
        ids = [i for i in csv.reader(f) if i][1:]
    for id_ in ids:
        if username in id_ and id_[2]:
            return {'password': id_[2]}
    return False


def apis_stu_twqd(user: dict):
    from BusinessLogicLayer.cluster.slavers.osh_slaver import stu_twqd

    user_ = {'username': user.get('username'), }

    # 启动节点任务,该操作为风险操作，权限越界，无需知道用户密码也可完成操作
    return stu_twqd(user_)


def apis_reload_superuser_cookie():
    from BusinessLogicLayer.cluster.slavers.Online_Service_Hall_submit import get_admin_cookie
    return get_admin_cookie()


def apis_stu_twqd_plus(user: dict):
    """
    当OSS没有截图时使用此接口
    既已知OSS没有截图，故无论osh-slaver如何执行，都要调用 osh-s上传截图
    :param user:
    :return:
    """
    from BusinessLogicLayer.cluster.slavers.Online_Service_Hall_submit import get_snp_and_upload
    from BusinessLogicLayer.cluster.slavers.osh_slaver import check_display_state, stu_twqd

    user_ = {'username': user.get('username'), }

    # 用户鉴权
    ttp = _select_user_table(user_["username"])
    if ttp:
        user_.update(ttp)
    else:
        return {'msg': 'failed', 'info': '用户权限不足', 'code': 101}

    # 使用osh-slaver判断用户是否签到
    # 若未签到，startup osh-main 进行签到；
    # 若已签到，end osh-main 结束子程序
    stu_state = check_display_state(user_)
    if stu_state['code'] != 902:
        stu_twqd(user_)

    # 启动Selenium上传截图 并返回调试数据
    return get_snp_and_upload(user_)
