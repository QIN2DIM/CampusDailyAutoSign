__all__ = ['runner']

from datetime import datetime, timedelta
from typing import Tuple

import requests

from src.BusinessCentralLayer.setting import TIME_ZONE_CN, logger, SERVER_PATH_COOKIES, OSH_STATUS_CODE
from src.BusinessLogicLayer.apis.manager_cookie import reload_admin_cookie


class _OshRunner(object):

    def __init__(self, cover: bool = False, debug: bool = False, **kwargs):
        """
        :param debug: 请不要再部署环境中开启debug
        :param cover: 重复提交。默认为False。这是一个非常危险的操作
        """
        self.cover = cover
        self.debug = debug
        self._state = kwargs.get("_state") if kwargs.get("_state") else 'YES'
        self._date = kwargs.get("_date") if kwargs.get("_date") else 0
        # API 调试接口
        self.API = 'https://ehall.hainanu.edu.cn/qljfwapp/sys/lwHainanuStuTempReport/*default/index.do#/stuTempReport'

        # API 调试接口 -- 测试cookie时效性
        self.api_checkCookie = 'https://ehall.hainanu.edu.cn/jsonp/ywtb/searchServiceItem?flag=0'

        # API 获取任务
        self.api_getStuTempReportData = 'https://ehall.hainanu.edu.cn/qljfwapp/sys/lwHainanuStuTempReport/mobile/stuTempReport/getStuTempReportData.do'

        # API 提交任务
        self.api_modifyStuTempReport = 'https://ehall.hainanu.edu.cn/qljfwapp/sys/lwHainanuStuTempReport/mobile/stuTempReport/T_STU_TEMP_REPORT_MODIFY.do?'

        self.headers_ = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66',
            'Host': 'ehall.hainanu.edu.cn',
            'Origin': 'https://ehall.hainanu.edu.cn',
            'Referer': 'https://ehall.hainanu.edu.cn/qljfwapp/sys/lwHainanuStuTempReport/*default/index.do',
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        }

        # COOKIE 直接访问API调试接口，然后在getStuTempReport的表单中复制cookie -- MOD_AMP_AUTH 可同时用于访问任务和提交任务
        self.super_user_cookie = self._load_super_user_cookie()

        # HEADERS 初始化越权cookie
        self.headers_['Cookie'] = self.super_user_cookie

    # ----------------------------------------------
    # Public API
    # ----------------------------------------------
    def get_stu_temp_report_data(self, username: str, headers_=None, only_check_status=False,
                                 _perm=False, _date: int = 0) -> dict or int:
        import random
        if headers_ is None:
            headers = self.headers_
        else:
            headers = headers_

        headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        data = {
            'USER_ID': username,  # 需要改动的用户名
            'pageNumber': 1,
            'pageSize': 10,
            'KSRQ': '2021-01-01',  # 查询起始日期
            'JSRQ': str(datetime.now(TIME_ZONE_CN)).split(' ')[0],  # 今天的日期,格式入KSRQ
        }

        def check_task_status() -> int:
            """
            # 判断是否已签到(非脚本操作)
            :return:
            """
            if stu_info['STATE'] == 'YES':
                return 902
            elif stu_info['STATE'] == 'NO':
                if datetime.fromisoformat(stu_info['CHECK_START_TIME']) > datetime.now(TIME_ZONE_CN).now():
                    return 901
                else:
                    return 903

        try:
            res = requests.post(self.api_getStuTempReportData, headers=headers, data=data)

            # 0：获取当日签到任务 1：获取昨日的，2：获取前日的.....
            stu_info: dict = res.json()['datas']['getStuTempReportData']['rows'][0]
            if only_check_status:
                stu_info: dict = res.json()['datas']['getStuTempReportData']['rows'][_date]

            # 预览请求数据，在debug模式下使用
            if self.debug:
                for i in stu_info.items():
                    print(i)

            # 查询任务状态:若已签到则结束程序
            if not self.cover:
                task_status = check_task_status()
                # 如果仅用于查看签到状态，无论状态如何，都结束执行，返回数据
                if only_check_status:
                    if _perm:
                        return stu_info
                    else:
                        return task_status
                if task_status != 903:
                    return task_status

            # FIXME 清洗Params:stu_info键值对包含学生个人隐私数据
            #  - CZR: 操作人学号 20221101201190
            #  - CZZXM: 操作人姓名 李二狗
            #  - CZRQ: 操作人cookie获取时间 2021-01-08 17:46:27
            #  -
            user_form = stu_info
            user_form.update(
                {
                    # TODO ： 断言当前时间是否超出任务时长限制
                    'REPORT_TIME': str(datetime.now(TIME_ZONE_CN)).split(".")[0][:-3],  # 上报当前时间戳

                    # TODO：这是一项较为危险的操作，若post->NO，意味着用户已成功打卡的表单将被重置，相当于将签到状态重置为NO
                    # 签到状态，YES:签到，NO:未签
                    'STATE': self._state,

                    # 不可更改
                    'BODY_TEMPERATURE_DISPLAY': '37.3°C以下',
                    'BODY_TEMPERATURE': '1',

                    # FIXME 权限交接--数据库复写，禁止渗透
                    'CZR': stu_info['USER_ID'],
                    'CZZXM': stu_info['USER_NAME'],
                    'CZRQ': str(datetime.now(TIME_ZONE_CN) - timedelta(seconds=random.randint(2, 25))).split(".")[0],
                }
            )

            # # 二级清洗
            del_uf = [uf for uf in stu_info.items() if uf[-1] is None]
            for duf in del_uf:
                del user_form[duf[0]]

            return user_form
        except requests.exceptions.TooManyRedirects:
            return 401
        except IndexError as e:
            # logger.exception(e)
            return 402
        except requests.exceptions.RequestException as e:
            logger.exception(e)

    @staticmethod
    def quick_refresh_cookie(user: dict = None) -> str:
        """
        从account中解析cookie
        :param user:username and password
        :return:
        """
        import base64
        import math
        import random
        import time
        import re
        from Crypto.Cipher import AES
        import requests

        def AESEncrypt(password, secret_key):
            def getRandomString(length):
                chs = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
                result = ''
                for o in range(0, length):
                    result += chs[(math.floor(random.random() * len(chs)))]
                return result

            def EncryptAES(s, middleware_key, iv='1' * 16, charset='utf-8'):
                middleware_key = middleware_key.encode(charset)
                iv = iv.encode(charset)
                block_size = 16

                def pad(p): return p + (block_size - len(p) % block_size) * chr(block_size - len(p) % block_size)

                raw = pad(s)
                cipher = AES.new(middleware_key, AES.MODE_CBC, iv)
                encrypted = cipher.encrypt(bytes(raw, encoding=charset))
                return str(base64.b64encode(encrypted), charset)

            return EncryptAES(getRandomString(64) + password, secret_key, secret_key)

        if user is None:
            from src.config import SUPERUSER
            user = SUPERUSER
        login_url = "https://ehall.hainanu.edu.cn/login?service=https://ehall.hainanu.edu.cn/ywtb-portal/Lite/index.html"

        time.sleep(0.3)
        r = requests.get(login_url)

        cookie = requests.utils.dict_from_cookiejar(r.cookies)
        cookie = 'route=' + cookie['route'] + '; JSESSIONID=' + cookie[
            'JSESSIONID'] + '; org.springframework.web.servlet.i18n.CookieLocaleResolver.LOCALE=zh_CN'
        header = {'Cookie': cookie}
        data = {
            'username': user['username'],
            'password': AESEncrypt(user['password'], re.findall('id="pwdDefaultEncryptSalt" value="(.*?)"', r.text)[0]),
            'lt': re.findall('name="lt" value="(.*)"', r.text)[0],
            'dllt': re.findall('name="dllt" value="(.*)"', r.text)[0],
            'execution': re.findall('name="execution" value="(.*?)"', r.text)[0],
            '_eventId': 'submit',
            'rmShown': re.findall('name="rmShown" value="(.*?)"', r.text)[0]
        }

        time.sleep(0.3)
        r = requests.post(r.url, headers=header, data=data, allow_redirects=False)
        location_ = r.headers['Location']
        header['Cookie'] += ("; CASTGC=" + requests.utils.dict_from_cookiejar(r.cookies)['CASTGC'])

        time.sleep(0.4)
        r = requests.get(location_, headers=header)
        key = {}
        for i in r.history:
            key.update(requests.utils.dict_from_cookiejar(i.cookies))
        superuser_cookie = f"MOD_AMP_AUTH={key['MOD_AMP_AUTH']}"
        with open(SERVER_PATH_COOKIES, 'w', encoding='utf-8') as f:
            f.write(superuser_cookie)
        return superuser_cookie

    @staticmethod
    def check_cookie(mod_amp_auth: str) -> bool:
        """
        检测superuser-cookie 是否过期
        :param mod_amp_auth:
        :return:
        """
        api_ = 'https://ehall.hainanu.edu.cn/jsonp/ywtb/searchServiceItem?flag=0'
        res = requests.get(api_, headers={'Cookie': mod_amp_auth})
        if res.json()['result'] == 'success':
            return True
        else:
            return False

    def run(self, user: dict = None) -> Tuple[int, dict]:
        """
        :param user: 传入学号键值对{'username':'学号’}
        :return: Tuple[int, dict] int为状态码，调用osh_status_code模块即可查看状态码含义
                dict为用户信息表，若执行成功则返回丰富数据。若程序中断，则返回传入的 param user
        """

        # ----------------------------------------------
        # Overload Headers
        # ----------------------------------------------
        headers_ = self.headers_

        # > Distinguish different behavior modes based on whether to pass in a password.
        # If you are a library user, use the user's cookie to access the system.
        # If not in the library, use the ultra vires check-in scheme (provide services for external interfaces).
        if user.get("password") and user.get("username"):
            # > The following are two solutions for detecting, updating, and reloading cookies, choose one to use
            # reload_admin_cookie  :Use Selenium (more mature, without frequent maintenance)
            # quick_refresh_cookie :Use the post method (faster but need to maintain the interface)
            from src.BusinessLogicLayer.apis.manager_cookie import reload_admin_cookie
            headers_['Cookie'] = reload_admin_cookie(user)[-1]
            # headers_['Cookie'] = self.quick_refresh_cookie(user)
        # ----------------------------------------------
        # Overload tasks
        # ----------------------------------------------
        params = self.get_stu_temp_report_data(user["username"], headers_=headers_)
        if isinstance(params, int):
            if self.debug:
                logger.warning(f'<OshRunner> {user["username"]} || {OSH_STATUS_CODE[params]}')
            return params, user
        # ----------------------------------------------
        # Submit task
        # ----------------------------------------------
        result = self._submit_task(user_form=params, headers_=headers_)
        if self.debug:
            if result == 300:
                logger.success(f'<OshRunner> {user["username"]} || {OSH_STATUS_CODE[result]}')
            else:
                logger.warning(f'<OshRunner> {user["username"]} || {OSH_STATUS_CODE[result]}')
        return result, params

    # ----------------------------------------------
    # Private API
    # ----------------------------------------------

    def _load_super_user_cookie(self, fp=SERVER_PATH_COOKIES):
        """

        :param fp: cookie路径，todo 修改存储规则
        :return:
        """
        # MOD_AMP_AUTH = 'MOD_AMP_AUTH=MOD_AMP_d03e09e1-7031-4ca3-94ce-548dff97ff40;'
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                mod_amp_auth = f.read()
        # 文件缺失
        except FileNotFoundError:
            return reload_admin_cookie()[-1]

        try:
            # 检测cookie是否可用
            # logger.debug(f"<OshRunner> Test the timeliness of the superuser's cookie -- {mod_amp_auth}")
            if mod_amp_auth:
                # cookie可用
                if self.check_cookie(mod_amp_auth):
                    return mod_amp_auth
                # cookie过期 启动子程序刷新cookie
                else:
                    logger.warning(f"<OshRunner> Superuser's cookie already expired！")
                    # 解决方案1：模拟登陆
                    # get_admin_cookie()
                    # 解决方案2：requests
                    self.quick_refresh_cookie()
                    return self._load_super_user_cookie(fp)
            # 文件中的cookie为空，需要重新写入
            else:
                # get_admin_cookie()
                self.quick_refresh_cookie()
                return self._load_super_user_cookie(fp)
        except Exception as e:
            logger.exception(e)

    def _submit_task(self, user_form: dict, headers_=None) -> int:
        """
        提交任务
        :param headers_:
        :param user_form: 提交的表单
        :return: int 状态码
        """
        if headers_ is None:
            headers_ = self.headers_
        from json.decoder import JSONDecodeError
        res = requests.post(self.api_modifyStuTempReport, headers=headers_, params=user_form)
        try:
            result = res.json()['datas']['T_STU_TEMP_REPORT_MODIFY']

            if self.debug:
                logger.info(res.json())

            if result == 1:
                if self.cover:
                    return 310
                else:
                    return 300
            else:
                return 305
        except JSONDecodeError:
            return 306


runner = _OshRunner
