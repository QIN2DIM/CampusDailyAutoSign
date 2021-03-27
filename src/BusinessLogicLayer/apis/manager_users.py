"""管理用户状态，包括但不限于查看签到状态，执行签到等"""
__all__ = ['apis_account_verify', 'check_display_state', 'stu_twqd']

import json

import requests

from src.BusinessCentralLayer.setting import OSH_STATUS_CODE, logger
from src.BusinessLogicLayer.cluster.osh_runner import runner


def apis_account_verify(user: dict):
    """
    验证今日校园账号正确

    :param user: username password
    :return:
    """

    logging_api = "http://www.zimo.wiki:8080/wisedu-unified-login-api-v1.0/api/login"

    apis_ = {
        'login-url': 'https://authserver.hainanu.edu.cn/authserver/login?service=https%3A%2F%2Fhainanu.campusphere.net%2Fiap%2FloginSuccess%3FsessionToken%3Df73b49371c0d4669aea95af37347e9fe',
        'host': 'hainanu.campusphere.net'
    }

    params = {
        'login_url': apis_['login-url'],
        'needcaptcha_url': '',
        'captcha_url': '',
        'username': user['username'],
        'password': user['password']
    }
    cookies = dict()
    try:
        res = requests.post(url=logging_api, data=params, timeout=2)
        cookie_str = str(res.json()['cookies'])
        if cookie_str == 'None':
            if "网页中没有找到casLoginForm" in res.json()['msg']:
                return None
            else:
                return False
        # 解析cookie
        for line in cookie_str.split(';'):
            name, value = line.strip().split('=', 1)
            cookies[name] = value
        session = requests.session()
        session.cookies = requests.utils.cookiejar_from_dict(cookies, cookiejar=None, overwrite=True)
        if session:
            return {'msg': 'success', 'info': 'Verified successfully'}
        else:
            return {'info': 'Incorrect username or password'}
    except json.decoder.JSONDecodeError or requests.exceptions.ProxyError:
        logger.warning("目标或存在鉴权行为，请关闭本地网络代理")


def check_display_state(user: dict, debug=False, _date=0) -> dict:
    """
    查询用户签到状态

    :param _date:
    :param user: only username
    :param debug:
    :return:
    """
    params = runner(debug=debug).get_stu_temp_report_data(
        username=user["username"],
        only_check_status=True,
        _date=_date
    )
    if isinstance(params, int):
        response = {'code': params, 'info': OSH_STATUS_CODE[params]}
        return response


def stu_twqd(user: dict, cover=False):
    """
    用于外部接口体温签到
    :param cover:
    :param user:仅传入username，越权；传入username and password 则使用该用户的cookie 进行操作
    :return:
    """
    params = runner(cover=cover, debug=False).run(user)
    response = {'code': params[0], 'info': f"{user['username']} -- {OSH_STATUS_CODE[params[0]]}"}
    return response

