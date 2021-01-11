__all__ = ['OshSlaver', 'check_display_state', 'stu_twqd']

from typing import Tuple
from datetime import datetime, timedelta

import requests
from BusinessLogicLayer.cluster.slavers.Online_Service_Hall_submit import osh_status_code, get_admin_cookie
from config import TIME_ZONE_CN, logger, SERVER_PATH_COOKIES


class OshSlaver(object):

    def __init__(self, cover: bool = False, debug: bool = False):
        """
        :param debug: 请不要再部署环境中开启debug
        :param cover: 重复提交。默认为False。这是一个非常危险的操作
        """
        self.cover = cover
        self.debug = debug

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
        self.super_user_cookie = self.load_super_user_cookie()

        # HEADERS 通用伪装头
        self.headers_['Cookie'] = self.super_user_cookie

    def load_super_user_cookie(self, fp=SERVER_PATH_COOKIES):
        """

        :param fp: cookie路径，todo 修改存储规则
        :return:
        """
        # MOD_AMP_AUTH = 'MOD_AMP_AUTH=MOD_AMP_d03e09e1-7031-4ca3-94ce-548dff97ff40;'
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                MOD_AMP_AUTH = f.read()

            # 检测cookie是否可用
            logger.debug(f'Test the timeliness of the superuser cookie -- {MOD_AMP_AUTH}')
            if MOD_AMP_AUTH:
                res = requests.get(self.api_checkCookie, headers={'Cookie': MOD_AMP_AUTH})
                # cookie可用，
                if res.json()['result'] == 'success':
                    logger.success(f'Load the superuser cookie -- {MOD_AMP_AUTH}')
                    return MOD_AMP_AUTH
                # cookie过期 启动子程序刷新cookie
                else:
                    logger.debug(f"superuser'cookie already expired ")
                    get_admin_cookie()
                    return self.load_super_user_cookie(fp)
            # 文件中的cookie为空，需要重新写入
            else:
                get_admin_cookie()
                return self.load_super_user_cookie(fp)
        # 文件缺失
        except FileNotFoundError:
            return get_admin_cookie()[-1]

    def get_stu_temp_report_data(self, username: str, only_check_status=False) -> dict or int:
        import random
        headers = self.headers_
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

            # 查询任务状态:若已签到则结束程序
            if not self.cover:
                task_status = check_task_status()
                # 如果仅用于查看签到状态，无论状态如何，都结束执行，返回数据
                if only_check_status:
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

                    # TODO：这是一项较为危险的操作，若post->NO，意味着用户已成功打卡的表单将被重置，相当于没签到
                    # 签到状态，YES:签到，NO:未签
                    'STATE': 'YES',

                    # 不可更改
                    'BODY_TEMPERATURE_DISPLAY': '37.3°C以下',
                    'BODY_TEMPERATURE': '1',

                    # 权限交接
                    'CZR': stu_info['USER_ID'],
                    'CZZXM': stu_info['USER_NAME'],
                    'CZRQ': str(datetime.now(TIME_ZONE_CN) - timedelta(seconds=random.randint(2, 25))).split(".")[0]
                }
            )

            # 二级清洗
            del_uf = [uf for uf in stu_info.items() if uf[-1] is None]
            for duf in del_uf:
                del user_form[duf[0]]

            # 预览请求数据，在debug模式下使用
            if self.debug:
                for i in user_form.items():
                    print(i)

            return user_form
        except requests.exceptions.TooManyRedirects:
            return 401
        except IndexError as e:
            logger.exception(e)
            return 402
        except requests.exceptions.RequestException as e:
            logger.exception(e)

    def submit_task(self, user_form: dict) -> int:
        """
        提交任务
        :param user_form: 提交的表单
        :return: int 状态码
        """
        from json.decoder import JSONDecodeError
        res = requests.post(self.api_modifyStuTempReport, headers=self.headers_, params=user_form)
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

    def run(self, user: dict = None) -> Tuple[int, dict]:
        """

        :param user: 传入学号键值对{'username':'学号’}
        :return: Tuple[int, dict] int为状态码，调用osh_status_code模块即可查看状态码含义
                dict为用户信息表，若执行成功则返回丰富数据。若程序中断，则返回传入的 param user
        """

        # 查询任务
        params = self.get_stu_temp_report_data(user["username"])
        if isinstance(params, int):
            logger.warning(f'{user["username"]} -- {osh_status_code[params]}')
            return params, user

        # 提交任务
        result = self.submit_task(user_form=params)
        if result == 300:
            logger.success(f'{user["username"]} -- {osh_status_code[result]}')
        else:
            logger.warning(f'{user["username"]} -- {osh_status_code[result]}')
        return result, params


def check_display_state(user: dict) -> dict:
    # 查询任务
    params = OshSlaver().get_stu_temp_report_data(user["username"], only_check_status=True)
    response = {'code': params, 'info': osh_status_code[params]}
    logger.info(f'{user["username"]} -- {response["info"]}')
    return response


def stu_twqd(user: dict, cover=False):
    """
    用于外部接口体温签到
    :param cover:
    :param user:
    :return:
    """
    params = OshSlaver(cover=cover, debug=False).run(user)
    response = {'code': params[0], 'info': f"{user['username']} -- {osh_status_code[params[0]]}"}
    logger.info(response['info'])
    return response