__all__ = ['HainanUniversity']

import base64
import json
import math
import os
import re
from datetime import datetime

import gevent
import requests
from gevent.queue import Queue
from requests.exceptions import *
from Crypto.Cipher import AES

from BusinessLogicLayer.cluster.master import ActionBase

from config import *

USE_PROXY = False
user_id = dict()
user_q = Queue()


class HainanUniversity(ActionBase):
    """海南大学驱动"""
    apis = {
        'login-url': 'https://authserver.hainanu.edu.cn/authserver/login?service=https%3A%2F%2Fhainanu.campusphere.net%2Fiap%2FloginSuccess%3FsessionToken%3Df73b49371c0d4669aea95af37347e9fe',
        'host': 'hainanu.campusphere.net'
    }

    def __init__(self):
        super(HainanUniversity, self).__init__()
        self.school_token = '海南大学'

        self.apis = {
            'login-url': 'https://authserver.hainanu.edu.cn/authserver/login?service=https%3A%2F%2Fhainanu.campusphere.net%2Fiap%2FloginSuccess%3FsessionToken%3Df73b49371c0d4669aea95af37347e9fe',
            'host': 'hainanu.campusphere.net'
        }
        self.proxies = dict()

        self.fork_api = self.get_session

    @staticmethod
    def AESEncrypt(data, secret_key):
        def getRandomString(length):
            chs = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
            result = ''
            for i in range(0, length):
                result += chs[(math.floor(random.random() * len(chs)))]
            return result

        def EncryptAES(s, middleware_key, iv='1' * 16, charset='utf-8'):
            middleware_key = middleware_key.encode(charset)
            iv = iv.encode(charset)
            BLOCK_SIZE = 16

            def pad(i): return i + (BLOCK_SIZE - len(i) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(i) % BLOCK_SIZE)

            raw = pad(s)
            cipher = AES.new(middleware_key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(bytes(raw, encoding=charset))
            return str(base64.b64encode(encrypted), charset)

        return EncryptAES(getRandomString(64) + data, secret_key, secret_key)

    def get_session_(self, user, apis=None, retry=0, delay=0.5, max_retry_num=100):

        if retry >= max_retry_num:
            logger.warning(f'[FAILED] 异常-- {user["username"]} || 教务接口异常')
            self.send_email('提醒您【手动打卡】\n'
                            '任务重试次数已达阈值！！\n'
                            '可能原因为:账号信息过时/线路拥堵/网络代理异常/IP封禁\n'
                            '<GoActionsID:1107>The Breathing-Rhythm Middleware has been activated to capture the '
                            'abnormal node.',
                            to=self.user_info['email'],
                            headers='<今日校园>提醒您【手动打卡】')
            return False

        if not apis:
            apis = self.apis
        """=============================替换====================================="""
        # PartI. -- loads login cookie
        response = requests.get(apis['login-url'], timeout=1)

        # PartI.-r -- 迂曲·监测教务接口
        try:
            cookie = requests.utils.dict_from_cookiejar(response.cookies)
            JSESSIONID = cookie['JSESSIONID']
            route = cookie['route']

            cookie = 'route=' + route + '; JSESSIONID=' + JSESSIONID + '; org.springframework.web.servlet.i18n' \
                                                                       '.CookieLocaleResolver.LOCALE=zh_CN '
            headers = {'Cookie': cookie}
        # 教务接口502
        except KeyError:
            logger.error('教务接口502')
            self.send_email('学校服务器又挂掉啦~\\(≧▽≦)/~（502伤心脸)\n' +
                            '<GoActionsID:1105>The Breathing Rhythm Middleware has been activated to capture the '
                            'abnormal node.',
                            to=self.user_info['email'],
                            headers='<今日校园>提醒您 -> 手动打卡')
            return False

        # PartII. -- loads session cookie
        try:
            response = requests.post(url=apis['login-url'], headers=headers, timeout=1)

        # IP may be frozen
        except ConnectionError or Timeout:
            retry += 1
            return self.get_session_(user, apis, retry)

        try:
            data = {
                'username': user['username'],
                'password': self.AESEncrypt(user['password'],
                                            re.findall('id="pwdDefaultEncryptSalt" value="(.*?)"', response.text)[0]),
                'lt': re.findall('name="lt" value="(.*)"', response.text)[0],
                'dllt': re.findall('name="dllt" value="(.*)"', response.text)[0],
                'execution': re.findall('name="execution" value="(.*?)"', response.text)[0],
                '_eventId': 'submit',
                'rmShown': re.findall('name="rmShown" value="(.*?)"', response.text)[0],
            }
        # IP was frozen
        except IndexError:
            retry += 1
            logger.debug(f'IP被封禁，线程休眠 {delay}s')
            gevent.sleep(delay)
            return self.get_session_(user, apis, retry, delay=300)

        cookies = dict()
        res = requests.post(url=apis['login-url'], headers=headers, data=data, allow_redirects=False)

        if res.status_code <= 400:
            Location = res.headers.get('Location')
            secret_key = requests.utils.dict_from_cookiejar(
                requests.get(url=f'https://{apis["host"]}/portal/login',
                             params={'ticket': re.findall('(?<==).*', Location)[0]},
                             allow_redirects=False).cookies
            )
            try:
                cookie_str = res.headers.get('SET-COOKIE')
                if not cookie_str:
                    retry += 1
                    gevent.sleep(delay)
                    return self.get_session_(user, apis, retry=retry, max_retry_num=max_retry_num, delay=delay)

                # 解析cookie
                for line in cookie_str.split(';'):
                    try:
                        name, value_ = line.replace(',', '').strip().split('=', 1)
                        if name == 'CASTGC' or name == 'CASPRIVACY':
                            cookies[name] = value_
                        elif 'iPlanetDirectoryPro' in name:
                            cookies['iPlanetDirectoryPro'] = value_.split('=')[-1]
                    except ValueError:
                        pass
                cookies.update({'route': route, 'JSESSIONID': JSESSIONID, })
                cookies.update(secret_key)
                """=============================替换====================================="""
                session = requests.session()
                session.cookies = requests.utils.cookiejar_from_dict(cookies, cookiejar=None, overwrite=True)
                return session

            # json提取异常，接口返回数据为空，重试(max_retry_num - 3)次
            except json.decoder.JSONDecodeError:
                return self.get_session_(user, apis, retry=max_retry_num - 3, delay=delay, max_retry_num=max_retry_num)

    def fill_form(self, task: dict, session, user, apis=None):
        form = {
            'longitude': LONGITUDE,
            'latitude': LATITUDE,
            'position': ADDRESS,
            'abnormalReason': ABNORMAL_REASON,
            'signPhotoUrl': ''
        }

        extraFields = task.get('extraField')
        if extraFields and extraFields.__len__() == 1:
            question = extraFields[0].get('title')
            answer = QnA[question]
            extraFieldItems = extraFields[0]['extraFieldItems']
            for extraFieldItem in extraFieldItems:
                if extraFieldItem['content'] == answer:
                    form['extraFieldItems'] = [{'extraFieldItemValue': answer,
                                                'extraFieldItemWid': extraFieldItem['wid']}]
        form['signInstanceWid'] = task['signInstanceWid']
        form['isMalposition'] = task['isMalposition']
        return form

    @staticmethod
    def private_extract(response: dict, user=None):
        """
        Obfuscated instructions
        :param user:
        :param response:
        :return:
        """
        global user_id
        user_id.update({user.get('username'): user})

        clear_response = {}

        for key_, value_ in response.get('signedStuInfo').items():
            if key_ in ['schoolStatus', 'malposition'] or value_ == '':
                continue
            clear_response.update({key_: value_})

        for key_, value_ in clear_response.items():
            if key_ == 'userId':
                user_id[value_].update(clear_response)
                user_id[value_].update({'request_time': str(datetime.now(TIME_ZONE_CN)).split('.')[0]})
                user_q.put_nowait(user_id[value_])

        if not user_q.empty():
            stu_info: dict = user_q.get_nowait()
            output = os.path.join(SERVER_DIR_CACHE, '{}.json'.format(stu_info['userId']))
            with open(output, 'w', encoding='utf8') as f:
                f.write(json.dumps(stu_info, indent=4, ensure_ascii=False))
            return stu_info

    def run(self, user=None):

        # loads user unified data
        self.user_info = user

        # (√) apis -- get the login url of AASoHainanU(Academic Affairs System of Hainan University)
        # self.apis = self.get_campus_daily_apis(user)

        # (√ A++Decoupling) session -- Simulated login the AASoHainanU
        session = self.fork_api(user, self.apis)

        # session success -- get the cookie and hold the session
        if session:
            params = self.get_unsigned_tasks(session)
            # (√) params success -- get the secret_key-des file of sign-in information
            if params:

                # (√) task -- sign in tasks(but only one)
                task = self.get_detail_task(session, params)

                # (*)stu_info -- extract private information of students
                self.user_info = self.private_extract(task, user)

                # (√) form -- requests post data
                form = self.fill_form(task, session, user)

                # (√) message -- API response json data
                message = self.submitForm(session, user, form)

                # message success -- (model output):task over!send notification SMS
                # TODO：Function Add: WeChat Push by <server Kishida>
                if message == 'SUCCESS':
                    logger.success("[SUCCESS] 签到 -- {}<{}> -- 自动签到成功".format(user['userName'], user['dept']))
                    # self.send_email('success', user['email'])
                # message error -- (ignore warning):The sign-in task of the next stage has not started
                # message error -- (stale panic):An unknown error occurred
                else:
                    if '任务未开始' not in message:
                        logger.critical("[PANIC] 签到 -- {} -- {}".format(user['username'], message))
                        # self.send_email('error', user['email'])
                    else:
                        # 任务未开始，扫码签到无效
                        logger.info("[IGNORE] 签到 -- {}<{}> -- 该用户本阶段任务已完成".format(user['userName'], user['dept']))

            # params error -- from the web interface of server.hainanu.net
            # params error -- The task for this student in the next time period is empty
            else:
                # print('The task for this student in the next time period is empty :{} '.format(user['username']))
                # self.send_email(self.error_msg, MANAGER_EMAIL)
                logger.debug("[FAILED] 签到 -- {} -- 该用户下个时间段无任务".format(user['username']))
                # logger.debug('Params is None||可能错误原因：该时间段无签到任务||{}'.format(user['username']))

        # session error -- Account error: user or password is None;user or password is mismatch
        # session error -- HTTP error: connection time out; too many retries
        else:
            if session is None:
                logger.info("[IGNORE] 失败 -- {} -- 该用户本阶段任务或已结束".format(user['username']))
            else:
                logger.warning('[FAILED] 异常 -- {} -- 账号或密码错误/教务接口异常/使用代理'.format(user['username']))
