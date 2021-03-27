__all__ = ['osh_core']

import time
from datetime import datetime
from os.path import join, exists
from typing import Tuple

from selenium.common.exceptions import *
from selenium.webdriver import Chrome, ChromeOptions, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.BusinessCentralLayer.middleware.flow_io import AliyunOSS
from src.BusinessCentralLayer.setting import *
from src.BusinessLogicLayer.plugins.faker_any import get_useragent


class _OnlineServiceHallSubmit(object):

    def __init__(self, silence=True, anti=True, debug=False, only_get_screenshot=True) -> None:

        self.url = 'https://ehall.hainanu.edu.cn/qljfwapp/sys/lwHainanuStuTempReport/*default/index.do#/stuTempReport'

        self.debug = debug
        self.only_get_screenshot = only_get_screenshot
        self.silence = silence
        self.anti = anti

        self.osh_model_today = join(SERVER_DIR_SCREENSHOT, str(datetime.now(TIME_ZONE_CN)).split(' ')[0])

        self._check_model()

    # ----------------------------------
    # Public API
    # ----------------------------------
    def rush_cookie_pool(self, user, kernel: str = 'admin') -> Tuple[int, str]:
        api_: Chrome = self._set_startup_option()

        try:
            # 模拟登入
            login_status = self._login(api_, user)
            if login_status == 302:
                logger.warning(f'FAILED -- {user["username"]}-- {OSH_STATUS_CODE[login_status]} -- 网络状况较差或OSH接口繁忙')
                return 302, user['username']
            # 获取SUPER_USER_COOKIE
            time.sleep(1)
            WebDriverWait(api_, 10).until(EC.element_located_to_be_selected)
            cookie: dict or None = api_.get_cookie('MOD_AMP_AUTH')
            # 若cookie有效则进行cookie缓存操作
            if cookie and isinstance(cookie, dict):
                user_cookie: str = f'{cookie.get("name")}={cookie.get("value")};'
                logger.info(f'Get Superuser Cookie -- {user_cookie}')
                # 根据不同的接入模式，使用不同的解决方案存储cookie
                if kernel == 'admin':
                    with open(SERVER_PATH_COOKIES, 'w', encoding='utf-8') as f:
                        f.write(user_cookie)
                elif kernel == 'general':
                    cache_path = os.path.join(SERVER_DIR_CACHE_FOR_TIMER, f'{user["username"]}.txt')
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(user_cookie)
                return 400, user_cookie
            else:
                return 403, user['username']
        finally:
            self._kill(api_)

    def run(self, user) -> Tuple[int, str] or Tuple[int, BaseException, str]:
        """
        服务器部署后，必须使用Silence Login 方案，而此时对于任务提交的调试有暂时无法攻克的技术难题
        故不要在部署后使用此模块进行表单提交，而应使用osh-runner
        :param user:
        :return:
        """

        # # 若今日已签到则无需登入
        # model_status = self._check_model(user, check_way='oss')
        # if model_status == 900:
        #     logger.info(f'<OshCore> IGNORE {user["username"]} || {OSH_STATUS_CODE[model_status]}')
        #     return model_status, user['username']

        # logger.info(f'<OshCore> Run OnlineServiceHallSubmit || {user["username"]}')

        # 共享任务句柄
        api_: Chrome = self._set_startup_option()

        try:
            # 模拟登入
            login_status = self._login(api_, user)
            if login_status == 302:
                logger.warning(
                    f'<OshCore> FAILED || 网络状况较差或OSH接口繁忙 || {user["username"]} {OSH_STATUS_CODE[login_status]}')
                return login_status, user['username']

            # 跳转到最新打卡页面
            stu_status: int = self._goto_sign_up(api_, user)

            # 在执行_goto_sign_up时已自动保存并上传任务页截图
            # 若启动该分支仅需完成此需求，请立即结束后续操作
            if self.only_get_screenshot:
                self.print_debug_msg("<OshCore> OnlyGetScreenshot || quick driver")
                return stu_status, user["username"]

            # 若需使用本分支执行签到操作，则根据“是否已签到”决定是否执行签到任务
            # 可签到 -> submit
            if stu_status == 903:
                self._submit(api_, user)
                return 300, user["username"]
            else:
                return stu_status, user["username"]

        # NoneType: 用户无任何待处理表单，意味着该用户不适用当前签到方案
        except TypeError as e:
            logger.warning(f'{user["username"]} -- {OSH_STATUS_CODE[304]}')
            return 304, e, user["username"]
        # 未知异常
        except WebDriverException as e:
            logger.exception(f'{user["username"]} -- {e}')
            return 301, e, user["username"]
        # 垃圾回收
        finally:
            self._kill(api_)

    # ----------------------------------
    # Private API
    # ----------------------------------

    def _check_model(self, user=None, check_way='init') -> bool or int:
        if check_way == 'init':
            if not exists(self.osh_model_today):
                os.mkdir(self.osh_model_today)
                logger.info(f'今日首次打卡进程启动，已初始化文档树')
                return True

        elif check_way == 'stale':
            if "{}.png".format(user['username']) in os.listdir(self.osh_model_today):
                return 900

        elif check_way == 'oss':
            if AliyunOSS().snp_exist(user['username']):
                return 900
        else:
            return False

    def _set_startup_option(self) -> Chrome:
        """
        ChromeDriver settings
        @return:
        """

        self.print_debug_msg("初始化驱动")

        options = ChromeOptions()

        # 最高权限运行
        options.add_argument('--no-sandbox')

        # 隐身模式
        options.add_argument('-incognito')

        # 无缓存加载
        # options.add_argument('--disk-cache-')

        # 设置中文
        options.add_argument('lang=zh_CN.UTF-8')

        options.add_experimental_option('excludeSwitches', ['enable-automation'])

        # 更换头部
        options.add_argument(f'user-agent={get_useragent()}')

        # 静默启动
        if self.silence is True:
            options.add_argument('--headless')

        if not self.anti:
            chrome_pref = {"profile.default_content_settings": {"Images": 2, 'javascript': 2},
                           "profile.managed_default_content_settings": {"Images": 2},
                           }
            options.experimental_options['prefs'] = chrome_pref

        return Chrome(options=options, executable_path=CHROMEDRIVER_PATH)

    def _login(self, api: Chrome, user, retry_num=0, max_retry=3) -> bool or int:

        # FIXME: 加入用户密码错误鉴别
        # 重试次数达到阈值
        if retry_num >= max_retry:
            return 302

        api.get(self.url)
        try:
            if not self.anti:
                time.sleep(1)
            WebDriverWait(api, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(
                user['username'])
            api.find_element_by_id('password').send_keys(user['password'])
            api.find_element_by_tag_name('button').click()

            self.print_debug_msg("模拟登录成功")
            return True
        except TimeoutException or NoSuchElementException:
            retry_num += 1
            api.refresh()
            self._login(api, user, retry_num)
        except StaleElementReferenceException:
            time.sleep(1.2)
            self._login(api, user, retry_num)

    @staticmethod
    def _check_status(element) -> int:
        """

        :param element: API定位的最新任务元素
        :return:
        """

        # 解压数据
        stu_missions = {}
        i = 1
        stu_info: list = element.text.split('\n')
        while i < element.text.split('\n').__len__() - 1:
            stu_missions.update({stu_info[i]: stu_info[i + 1]})
            i += 2

        # 今日签到任务tag已成功定位，但未抵达任务开放时间，此时默认上报状态为false
        if datetime.fromisoformat(stu_missions.get('上报开始时间')) > datetime.now(TIME_ZONE_CN).now():
            return 901
        else:
            # 今日/昨日 任务已签到
            if stu_missions.get('是否上报') == '是':
                return 902
            # 今日/昨日 任务未签到
            elif stu_missions.get('是否上报') == '否':
                return 903

        # if stu_missions.get('是否上报') == '是':
        #     return 902
        # elif stu_missions.get('是否上报') == '否':
        #     if datetime.fromisoformat(stu_missions.get('上报开始时间')) > datetime.now(TIME_ZONE_CN).now():
        #         return 901
        #     else:
        #         return 903

    def print_debug_msg(self, msg: str):
        if self.debug:
            print(msg)

    def _goto_sign_up(self, api: Chrome, user=None, retry_num=0, max_retry=3) -> int:
        """

        :param api:
        :param user:
        :param retry_num:
        :param max_retry:
        :return:
        """
        # 超时中断
        if retry_num >= max_retry:
            logger.debug(f'FAILED -- {user["username"]}-- 该测试用例异常，可能原因为：账号密码错误或网络异常')
            return False

        try:
            # 获取最新任务tag
            time.sleep(1)
            latest_mission = WebDriverWait(api, 50).until(EC.presence_of_element_located((
                By.XPATH,
                "//div[@class='mint-layout-container cjarv696w']"
            )))

            # 查询任务状态
            task_status = self._check_status(latest_mission)

            # 可签到
            if task_status == 903:
                if self.only_get_screenshot:
                    logger.error(f"<OshCore> {user['username']} || 截图捕获失败，今日签到任务未执行。")
                latest_mission.click()

            # 已签到
            elif task_status == 902:
                # logger.info(f"{user['username']} -- {OSH_STATUS_CODE[task_status]}")
                self._save_log(api, user)
                # logger.success(f"{user['username']} -- 截图上传成功")

            # 未开放
            elif task_status == 901:
                logger.warning(f'{user["username"]} -- {OSH_STATUS_CODE[task_status]}')
            return task_status

        # 元素更新/任务超时/网络通信异常
        except NoSuchElementException or TimeoutException:
            retry_num += 1
            logger.debug(f'{user["username"]} -- 任务超时，重试次数{retry_num}')
            self._goto_sign_up(api, retry_num=retry_num)

    def _submit(self, api: Chrome, user=None):

        def _scroll_the_window():
            actions = ActionChains(api)
            actions.key_down(Keys.END).perform()
            actions.reset_actions()

        def _click_temperature_selection_bar(retry=0, max_retry=10):
            try:
                time.sleep(1)
                _scroll_the_window()
                api.find_element_by_xpath("//div[@class='__em-selectlist']").click()
            except ElementClickInterceptedException:
                if retry <= max_retry:
                    retry += 1
                    _click_temperature_selection_bar(retry=retry)

        def _click_confirm_button_of_the_temperature():
            time.sleep(1)
            api.find_element_by_xpath("//div[@visible-item-count]//div[contains(@class,'confirm')]").click()

        def _click_submit_button_of_the_temperature():
            time.sleep(0.5)
            api.find_element_by_xpath(
                "//button[@class='mint-button flowEditButton mt-btn-primary mint-button--normal']").click()

        def _click_submit_button_of_the_form():
            try:
                self.print_debug_msg("尝试捕获弹窗")
                time.sleep(0.5)
                err_ = api.find_element_by_xpath("//div[contains(@class,'mint-msgbox-message')]")
                # api.find_element_by_class_name("mint-msgbox-content").text
                if err_ is not None:
                    logger.error(f"<OshCore> {user['username']} || {err_.text}")
            except NoSuchElementException:
                print("123123123")
                pass

            time.sleep(0.5)
            api.find_element_by_xpath("//button[@class='mint-msgbox-btn mint-msgbox-confirm mt-btn-primary']").click()

        def _generate_behavior_response():
            response = self._save_log(api, user, status_='goto')
            if response:
                logger.success(f"<OshCore> {user['username']} || 签到成功")
            else:
                logger.warning(f"<OshCore> {user['username']} || 签到异常")

        # 进入[体温签到页面]
        api.find_element_by_id("app").click()
        self.print_debug_msg("进入[体温签到页面]")

        # 点击[体温选择栏]
        _click_temperature_selection_bar()
        self.print_debug_msg("点击[体温选择栏]")

        # [确认]体温
        _click_confirm_button_of_the_temperature()
        self.print_debug_msg("[确认]体温")

        # 点击[提交数据]按钮
        _click_submit_button_of_the_temperature()
        self.print_debug_msg("点击[提交数据]按钮")

        # 点击[确认提交数据]按钮
        _click_submit_button_of_the_form()
        self.print_debug_msg("点击[确认提交数据]按钮")

        # 判断签到状态 并上传截图
        _generate_behavior_response()
        self.print_debug_msg("判断签到状态 并上传截图")

    def _save_log(self, api: Chrome, user, status_='wait') -> bool:
        """

        :param api:
        :param user:
        :param status_: wait:已签到 ，goto：刚签到，返回上一级后截图
        :return:
        """

        if status_ == 'wait':
            api.save_screenshot(join(self.osh_model_today, f"{user['username']}.png"))
            AliyunOSS().upload_base64(api.get_screenshot_as_base64(), user['username'])
            return True
        elif status_ == 'goto':
            api.back()
            time.sleep(0.5)
            if self._check_status(api.find_element_by_xpath("//div[@class='mint-layout-container cjarv696w']")) == 902:
                self._save_log(api, user)
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def _kill(api: Chrome) -> None:
        api.delete_all_cookies()
        api.quit()


osh_core = _OnlineServiceHallSubmit
