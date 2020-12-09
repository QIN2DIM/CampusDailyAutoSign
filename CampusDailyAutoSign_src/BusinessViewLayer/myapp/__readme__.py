"""
该模块编写API调用规范
"""
__all__ = ['']

from json.decoder import JSONDecodeError

import requests

from config import *

ip_ = API_HOST
port_ = API_PORT


# 端口参数封装
def __detection__(response) -> dict or bool:
    try:
        return response.json()
    except JSONDecodeError:
        return None


# 验证账号密码是否填写正确
def check_passable(user: dict) -> dict or bool:
    """验证账号密码是否正确"""
    url = f'http://{ip_}:{port_}{ROUTE_API["verity_cpdaily_account"]}'
    return __detection__(requests.post(url, data=user))


# 验证学号是否已注册
def check_register(username: str) -> dict or bool:
    """验证该学号是否已注册"""
    url = f'http://{ip_}{port_}{ROUTE_API["verity_account_exist"]}'
    return __detection__(requests.post(url, data=username))


# 验证邮箱是否合法
def check_email(email: str) -> dict or bool:
    url = f'http://{ip_}{port_}{ROUTE_API["verity_email_passable"]}'
    return __detection__(requests.post(url, data=email))


# 前端调用示例
def test_logic() -> None:
    import sys

    sys.path.append('..')
    import requests
    from config import ROUTE_API
    interface = "http://127.0.0.1:6600"

    # TODO 0.假设这是个前端网页，开始接受数据
    user_ = {
        'school': '海南大学',
        'username': input(">> 请输入您的学号："),
        'password': input(">> 请输入您的密码："),
    }

    # TODO 1.验证账号是否已在库
    res_exist = requests.post(f"{interface}{ROUTE_API['verity_account_exist']}", data=user_)

    # 若账号可登记则继续执行
    if res_exist.json()['msg'] == 'success':
        # print(">> 账号可登记")

        # TODO 2.验证账号是否正确
        res_account = requests.post(f"{interface}{ROUTE_API['verity_cpdaily_account']}", data=user_)

        # 若账号信息无误则继续执行
        if res_account.json()['msg'] == 'success':
            # print(">> 账号信息正确")

            # TODO 3.验证邮箱 -> if success response token
            user_.update({'email': input(">> 请输入您的通信邮箱：")})
            res_email = requests.post(f"{interface}{ROUTE_API['verity_email_passable']}", data=user_)
            if res_email.json()['msg'] == 'success':

                # {'token': '9027c84d-b18c-41e1-a3ec-a551182c97e3'}
                # 获取Token，并更新用户表
                user_.update({'token': res_email.json()['token']})

                # TODO 4.携带Token发出请求，服务器验证Token，比对邮箱数据
                # 若密钥适配，则发送验证码
                res_post_code = requests.post(f"{interface}{ROUTE_API['send_verity_code']}", data=user_)

                # 验证码发送成功，由用户手动输入验证码(sid)
                if res_post_code.json()['msg'] == 'success':
                    print('>> 邮箱验证码已发送 请注意查收')

                    # 将用户输入的验证码(sid)更新用户表(user_)
                    user_.update({'sid': input(">> 请输入验证码：")})

                    # TODO 5.携带所有信息发起最后的验证请求，该请求验证(二步验证)通过后则触发ADD_USER机制
                    res_add = requests.post(f"{interface}{ROUTE_API['add_user']}", data=user_)
                    if res_add.json()['msg'] == 'success':
                        # 账号入库成功，若此项success 再次执行提交程序 应返回failed 并提示账号已登记
                        print(res_add.json()['info'])

    else:
        ...
