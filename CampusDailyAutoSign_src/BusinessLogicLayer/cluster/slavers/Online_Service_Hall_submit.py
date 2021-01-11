__all__ = ['osh_status_code', 'OnlineServiceHallSubmit', 'get_snp_and_upload', 'get_admin_cookie', 'AliyunOSS']

import time
from os.path import join, exists
import os
from datetime import datetime
from typing import Tuple

from selenium.common.exceptions import *
from selenium.webdriver import Chrome, ChromeOptions, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from config import logger, CHROMEDRIVER_PATH, SERVER_DIR_SCREENSHOT, TIME_ZONE_CN, ACKEY, SERVER_PATH_COOKIES

import oss2

osh_status_code = {
    # 应立即结束任务
    900: '任务劫持。该用户今日签到数据已在库',
    901: '任务待提交。今日签到任务已出现，但未抵达签到开始时间。',

    # 应直接在当前列表调用截图上传模块
    902: '任务已提交。任务状态显示用户已签到。',

    # 调用主程序完成签到任务
    903: '任务待提交。任务出现并抵达开始签到时间。',
    904: '',

    # 任务句柄
    300: '任务提交成功。通过OSH签到成功。',
    301: '任务提交失败。出现未知错误。',
    302: '任务提交失败。重试次数超过阈值',
    303: '任务提交失败。Selenium操作超时',
    304: '任务提交失败。该用户不使用网服大厅进行签到。具体表现为日期范围内的打卡任务全为空。',
    305: '任务提交失败。T_STU_TEMP_REPORT_MODIFY 返回值为0。',

    306: '任务解析异常。Response解析json时抛出的JSONDecodeError错误，根本原因为返回的datas为空。可能原因为：接口变动，网络超时，接口参数变动等。',
    310: '任务重置成功。使用Response越权操作，重置当前签到任务。',

    400: '刷新成功。成功获取Superuser Cookie!',
    401: '登录失败。AdminCookie stale! 超级用户COOKIE过时/错误/文件不在目标路径。',
    402: '登录失败。OSH_IP 可能已被封禁！',
    403: '更新失败。MOD_AMP_AUTH获取异常，可能原因为登陆成功但未获取关键包',

    500: '体温截图上传成功。',
    501: '体温截图获取失败。可能原因为上传环节异常或登录超时（账号有误，操作超时）'
}


class OnlineServiceHallSubmit(object):

    def __init__(self, silence=True, anti=True) -> None:

        self.url = 'https://ehall.hainanu.edu.cn/qljfwapp/sys/lwHainanuStuTempReport/*default/index.do#/stuTempReport'

        self.silence = silence

        self.anti = anti

        self.osh_model_today = join(SERVER_DIR_SCREENSHOT, str(datetime.now(TIME_ZONE_CN)).split(' ')[0])

        self.__check_model__()

    def __check_model__(self, user=None, check_way='init') -> bool or int:
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

    def __set_spider_option__(self) -> Chrome:
        """
        ChromeDriver settings
        @return:
        """

        options = ChromeOptions()

        # 最高权限运行
        options.add_argument('--no-sandbox')

        # 隐身模式
        options.add_argument('-incognito')

        # 无缓存加载
        options.add_argument('--disk-cache-')

        # 设置中文
        options.add_argument('lang=zh_CN.UTF-8')

        options.add_experimental_option('excludeSwitches', ['enable-automation'])

        # 更换头部
        # options.add_argument(f'user-agent={get_header()}')

        # 静默启动
        if self.silence is True:
            options.add_argument('--headless')

        if not self.anti:
            chrome_pref = {"profile.default_content_settings": {"Images": 2, 'javascript': 2},
                           "profile.managed_default_content_settings": {"Images": 2},
                           }
            options.experimental_options['prefs'] = chrome_pref

        return Chrome(options=options, executable_path=CHROMEDRIVER_PATH)

    def __login__(self, api: Chrome, user, retry_num=0, max_retry=3) -> bool or int:

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
            return True
        except TimeoutException or NoSuchElementException:
            retry_num += 1
            api.refresh()
            self.__login__(api, user, retry_num)
        except StaleElementReferenceException:
            time.sleep(1.2)
            self.__login__(api, user, retry_num)

    @staticmethod
    def __check_status__(element) -> int:
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

        # 判断是否已签到(非脚本操作)
        if stu_missions.get('是否上报') == '是':
            return 902
        elif stu_missions.get('是否上报') == '否':
            if datetime.fromisoformat(stu_missions.get('上报开始时间')) > datetime.now(TIME_ZONE_CN).now():
                return 901
            else:
                return 903

    def __goto_sign_up__(self, api: Chrome, user=None, retry_num=0, max_retry=3) -> int:
        """

        :param api:
        :param user:
        :param retry_num:
        :param max_retry:
        :return:
        """
        if retry_num >= max_retry:
            logger.debug(f'FAILED -- {user["username"]}-- 该测试用例异常，可能原因为：账号密码错误或网络异常')
            return False

        try:
            time.sleep(1)
            latest_mission = WebDriverWait(api, 50).until(EC.presence_of_element_located((
                By.XPATH,
                "//div[@class='mint-layout-container cjarv696w']"
            )))

            # 查询任务状态
            task_status = self.__check_status__(latest_mission)
            if task_status == 903:
                latest_mission.click()
            else:
                if task_status == 902:
                    logger.info(f'{user["username"]} -- {osh_status_code[task_status]}')
                    self.__save_log__(api, user)
                    logger.info(f'{user["username"]} -- 截图已备份')
                else:
                    logger.warning(f'{user["username"]} -- {osh_status_code[task_status]}')
            return task_status

        # 元素更新/任务超时/网络通信异常
        except NoSuchElementException or TimeoutException:
            retry_num += 1
            logger.debug(f'{user["username"]} -- 任务超时，重试次数{retry_num}')
            self.__goto_sign_up__(api, retry_num=retry_num)

    def __submit__(self, api: Chrome, user=None, retry_num=0, max_retry=3):
        if retry_num > max_retry:
            return False

        try:
            actions = ActionChains(api)
            time.sleep(0.5)
            # 点击体温选择栏
            action1 = api.find_element_by_xpath("//div[@class='mt-color-grey-lv3']")
            # action1 = WebDriverWait(api, 10).until(EC.presence_of_element_located((
            #     By.XPATH,
            #     "//div[@class='__em-selectlist']"
            # )))
            # api.execute_script("arguments[0].click();", action1)
            actions.move_to_element(action1).click_and_hold(action1).release(action1).perform()

            # action1.click()

            # 选择体温并确认
            time.sleep(1)
            action2 = api.find_element_by_xpath("//div[@visible-item-count]//div[contains(@class,'confirm')]")
            # action2 = WebDriverWait(api, 10).until(EC.presence_of_element_located((
            #     By.XPATH,
            #     "//div[@visible-item-count]//div[contains(@class,'confirm')]"
            # )))
            # api.execute_script("arguments[0].click();", action2)

            # actions.move_to_element(action2).click(action2).perform()
            action2.click()

        except TimeoutException or NoSuchElementException:
            logger.info(f'IGNORE -- {user["username"]} -- 该用户已填报')
            return True
        except ElementClickInterceptedException:
            time.sleep(2)
            retry_num += 1
            self.__submit__(api, user, retry_num)
            # logger.warning(f'FAILED -- {user["username"]} -- 签到异常')

        # 提交数据
        time.sleep(0.5)
        action3 = WebDriverWait(api, 10).until(EC.presence_of_element_located((
            By.XPATH,
            "//button[@class='mint-button flowEditButton mt-btn-primary mint-button--normal']"
        )))
        # api.execute_script("arguments[0].click();", action3)
        ActionChains(api).move_to_element(action3).click(action3).perform()
        # action3.click()

        # 确认提交数据
        time.sleep(0.5)
        action4 = WebDriverWait(api, 2).until(EC.presence_of_element_located((
            By.XPATH,
            "//button[@class='mint-msgbox-btn mint-msgbox-confirm mt-btn-primary']"
        )))
        # api.execute_script("arguments[0].click();", action4)
        ActionChains(api).move_to_element(action4).click(action4).perform()
        # action4.click()

        logger.success(f'SUCCESS -- {user["username"]} -- 签到成功')

        self.__save_log__(api, user, status_='goto')

    def __save_log__(self, api: Chrome, user, status_='wait') -> bool:
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
            self.__save_log__(api, user)
        else:
            return False

    @staticmethod
    def __kill__(api: Chrome) -> None:
        api.delete_all_cookies()
        api.quit()

    def rush_cookie_pool(self, user) -> Tuple[int, str]:
        api_: Chrome = self.__set_spider_option__()

        try:
            # 模拟登入
            login_status = self.__login__(api_, user)
            if login_status == 302:
                logger.warning(f'FAILED -- {user["username"]}-- {osh_status_code[login_status]} -- 网络状况较差或OSH接口繁忙')
                return 302, user['username']

            # 获取SUPER_USER_COOKIE
            time.sleep(1)
            WebDriverWait(api_, 10).until(EC.element_located_to_be_selected)

            cookie: dict or None = api_.get_cookie('MOD_AMP_AUTH')
            if cookie and isinstance(cookie, dict):
                user_cookie: str = f'{cookie.get("name")}={cookie.get("value")};'
                logger.info(f'Get Superuser Cookie -- {user_cookie}')
                with open(SERVER_PATH_COOKIES, 'w', encoding='utf-8') as f:
                    f.write(user_cookie)
                return 400, user_cookie
            else:
                return 403, user['username']
        finally:
            self.__kill__(api_)

    def upload_snp(self, user) -> Tuple[int, str]:
        """
        请在已知体温已签到的情况下调用此模块。否则可能上传签到状态为否的截图！
        :param user:
        :return:
        """
        if AliyunOSS().snp_exist(user["username"]):
            logger.warning(f"{user['username']} -- OSS已存在用户体温签到截图，此操作将覆盖云端数据！")

        api_: Chrome = self.__set_spider_option__()
        try:
            # 模拟登入
            login_status = self.__login__(api_, user)
            if login_status == 302:
                logger.warning(f'FAILED -- {user["username"]}-- {osh_status_code[login_status]} -- 网络状况较差或OSH接口繁忙')
                return 302, user['username']
            # WebDriverWait(api_, 10).until(EC.presence_of_all_elements_located)
            # WebDriverWait(api_, 10).until(EC.element_located_to_be_selected)
            time.sleep(10)
            self.__save_log__(api_, user)
            return 500, user["username"]
        except WebDriverException:
            return 501, user["username"]
        finally:
            self.__kill__(api_)

    def run(self, user, only_get_snp=True) -> Tuple[int, str] or Tuple[int, BaseException, str]:
        """
        服务器部署后，必须使用Silence Login 方案，而此时对于任务提交的调试有暂时无法攻克的技术难题
        故不要再部署后使用此模块进行表单提交，而应使用osh_slaver
        :param user:
        :param only_get_snp:
        :return:
        """

        # 今日已签到，无需登入
        model_status = self.__check_model__(user, check_way='oss')
        if model_status == 900:
            logger.info(f'IGNORE -- {user["username"]} -- {osh_status_code[model_status]}')
            return model_status, user['username']
        else:
            logger.info(f'Run -- OnlineServiceHallSubmit -- {user["username"]}')

        # 创建任务API
        api_: Chrome = self.__set_spider_option__()
        try:

            # 模拟登入
            login_status = self.__login__(api_, user)
            if login_status == 302:
                logger.warning(f'FAILED -- {user["username"]}-- {osh_status_code[login_status]} -- 网络状况较差或OSH接口繁忙')
                return login_status, user['username']

            # 跳转到最新打卡页面
            stu_status: int = self.__goto_sign_up__(api_, user)
            if only_get_snp:
                return 300, user['username']
            if stu_status == 903:
                self.__submit__(api_, user)
                return 300, user["username"]
            else:
                return stu_status, user["username"]

        # NoneType: 用户无任何待处理表单，意味着该用户不适用当前签到方案
        except TypeError as e:
            logger.warning(f'{user["username"]} -- {osh_status_code[304]}')
            return 304, e, user["username"]
        # 未知异常
        except WebDriverException as e:
            logger.exception(f'{user["username"]} -- {e}')
            return 301, e, user["username"]
        # 垃圾回收
        finally:
            self.__kill__(api_)


class AliyunOSS(object):

    def __init__(self):
        AccessKeyId = ACKEY['id']
        AccessKeySecret = ACKEY['secret']
        auth = oss2.Auth(AccessKeyId, AccessKeySecret)
        bucket_name = ACKEY['bucket_name']
        self.bucket = oss2.Bucket(auth, ACKEY['endpoint'], bucket_name)

        self.osh_day = str(datetime.now(TIME_ZONE_CN)).split(" ")[0]
        self.root_obj = f'cpds/api/stu_snp/{self.osh_day}/'

    def upload_base64(self, content: str, username: str):
        result = self.bucket.put_object(f'{self.root_obj}{username}.txt', content)

        # # HTTP返回码。
        # print('http status: {0}'.format(result.status))
        # # 请求ID。请求ID是请求的唯一标识，强烈建议在程序日志中添加此参数。
        # print('request_id: {0}'.format(result.request_id))
        # # ETag是put_object方法返回值特有的属性，用于标识一个Object的内容。
        # print('ETag: {0}'.format(result.etag))
        # # HTTP响应头部。
        # print('date: {0}'.format(result.headers['date']))

    def snp_exist(self, username):
        return self.bucket.object_exists(f'{self.root_obj}{username}.txt')

    def download_snp(self, username):
        if self.snp_exist(username):
            self.bucket.get_object_to_file(f'{self.root_obj}{username}.txt', SERVER_DIR_SCREENSHOT + f'/{username}.txt')
        else:
            return False


def get_admin_cookie() -> Tuple[int, str]:
    from config import SUPERUSER
    logger.debug('Reload Superuser Cookie...')
    return OnlineServiceHallSubmit(silence=True, anti=False).rush_cookie_pool(SUPERUSER)


def get_snp_and_upload(user: dict) -> dict:
    params = OnlineServiceHallSubmit(silence=True, anti=False).run(user, only_get_snp=True)
    response = {'code': params[0], 'username': params[-1], 'info': osh_status_code[params[0]]}
    logger.info(f"{params[-1]} -- {osh_status_code[params[0]]}")
    return response
