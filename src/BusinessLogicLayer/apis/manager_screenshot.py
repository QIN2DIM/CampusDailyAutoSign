__all__ = ['UploadScreenshot', 'capture_and_upload_screenshot']

import sys

sys.path.append("/qinse/CpdsNonebot")

import requests

from src.BusinessCentralLayer.setting import logger, OSH_STATUS_CODE, API_PORT, API_HOST, PUBLIC_API_STU_TWQD2
from src.BusinessLogicLayer.cluster.osh_core import osh_core


def capture_and_upload_screenshot(user: dict, silence=True, only_get_screenshot: bool = True, debug=False) -> dict:
    """
    通过模拟登陆的方案获取签到截图，并上传oss
    :param debug:
    :param only_get_screenshot:使用Selenium上传已签到截图（若今日签到任务未完成则不能执行）
    :param user: username and password
    :param silence:
    :return:
    """
    params = osh_core(silence=silence, anti=False, debug=debug, only_get_screenshot=only_get_screenshot).run(user)
    response = {'code': params[0], 'username': params[-1], 'info': OSH_STATUS_CODE[params[0]]}
    # logger.info(f"{params[-1]} -- {OSH_STATUS_CODE[params[0]]}")
    return response


class UploadScreenshot(object):
    def __init__(self):
        self.api_ = f"http://{API_HOST}:{API_PORT}{PUBLIC_API_STU_TWQD2}"
        # self.api_ = 'http://twqd.yaoqinse.com:6577/cpds/api/stu_twqd2'

    def run(self, user):
        """

        :param user:{"username":, "password":str}
        :return:
        """
        resp = requests.post(self.api_, data=user)
        response = resp.json()
        if response.get("code") == 300:
            logger.success(f'{response.get("username")} -- {response.get("info")}')
        else:
            logger.success(f'{response.get("username")} -- {response.get("info")}')

