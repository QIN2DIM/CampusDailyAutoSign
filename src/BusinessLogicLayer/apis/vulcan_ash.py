__all__ = ['SignInWithScreenshot', 'SignInSpeedup']

from typing import List

from requests.exceptions import *

from src.BusinessCentralLayer.coroutine_engine import lsu_
from src.BusinessCentralLayer.setting import logger


class SignInSpeedup(lsu_):
    """用于越权签到的轻量化协程加速控件"""

    def __init__(self, task_docker: List[dict], power=2):
        """

        :param task_docker: 装有学号的列表
        """
        super(SignInSpeedup, self).__init__(task_docker=task_docker, power=power)

        from src.BusinessLogicLayer.apis.manager_users import stu_twqd
        self.core_ = stu_twqd

    def offload_task(self):
        for task in self.task_docker:
            self.work_q.put_nowait(task)

    def control_driver(self, user: dict):
        """

        :param user: {"username":str } or {"username":str ,"password":str }
        :return:
        """

        try:
            # 为账号开辟原子级实例，避免因高并发引起的共享重用问题
            response = self.core_(user=user, cover=False)
            logger.success(f"<VulcanAsh> FinishTank (N/{self.work_q.qsize()}) || {response['info']}")

        except IndexError or KeyError or ConnectionError:
            # 数据容灾
            logger.error(f"<OshRunner> {user['username']} || cookie更新失败 请求频次过高 IP可能被封禁")
            self.ddt(task=user)

    def ddt(self, task: dict):
        """
        用于集群容载或IP共享
        :return:
        """
        # TODO 方案1 通过HTTP接口请求同伴服务器，确保参数同步
        import requests
        from src.BusinessCentralLayer.setting import API_PORT, API_SLAVES, PUBLIC_API_STU_TWQD
        from threading import Thread
        atomic = API_SLAVES.copy().pop()
        if atomic:
            slave_api = f"http://{atomic}:{API_PORT}{PUBLIC_API_STU_TWQD}"
            Thread(target=requests.post, kwargs={"url": slave_api, "data": task}).start()
            logger.debug(f"<SignInSpeedup> {task['username']} -> slaves")
        else:
            # 本机挂起IP解封静默措施
            logger.warning(f"<SignInSpeedup> {task['username']} || BeatSync 300s")
            self.work_q.put(task)
            self.beat_sync(sleep_time=300)

        # TODO 方案2 通过配置Redis实现端到端订阅发布，并由slave节拍同步消解任务

        # TODO 方案3 通过REC交流数据


class SignInWithScreenshot(SignInSpeedup):
    """用于伴随截图上传需求的加速控件"""

    def __init__(self, task_docker: List[dict], power=2):
        super(SignInWithScreenshot, self).__init__(task_docker=task_docker, power=power)

        from src.BusinessLogicLayer.apis.manager_screenshot import capture_and_upload_screenshot
        from src.BusinessLogicLayer.apis.manager_users import check_display_state

        self.plugin_upload_screenshot = capture_and_upload_screenshot
        self.plugin_check_state = check_display_state

    def control_driver(self, user: dict):
        try:

            # 检测签到状态
            if self.plugin_check_state(user)['code'] != 902:
                # 为账号开辟原子级实例，避免因高并发引起的共享重用问题
                self.core_(user=user, cover=False)

            # 截图上传
            self.release_plugin_upload_screenshot(user=user)

        except IndexError or KeyError or RequestException:
            logger.error(f"<OshRunner> {user['username']} || cookie更新失败 请求频次过高 IP可能被封禁")

            # 数据容灾
            self.ddt(task=user)

    def release_plugin_upload_screenshot(self, user: dict):
        self.plugin_upload_screenshot(user=user, silence=True)
