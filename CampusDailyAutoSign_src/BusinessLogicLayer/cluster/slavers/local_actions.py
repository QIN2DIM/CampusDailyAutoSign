__all__ = ['NoCloudAction']

import base64
import json
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse

import requests
from pyDes import des, CBC, PAD_PKCS5

from BusinessCentralLayer.sentinel.noticer import send_email
from BusinessLogicLayer.cluster.slavers.hainanu import HainanUniversity
from config import TIME_ZONE_CN, SECRET_NAME, logger


class NoCloudAction(object):

    def __init__(self):
        self.get_data_url = "https://hainanu.campusphere.net/wec-counselor-sign-apps/stu/sign/queryDailySginTasks"
        self.detial_url = "https://hainanu.campusphere.net/wec-counselor-sign-apps/stu/sign/detailSignTaskInst"
        self.signurl = "https://hainanu.campusphere.net/wec-counselor-sign-apps/stu/sign/completeSignIn"

        self.user_info = {}
        self.apis = {
            'login-url': "https://hainanu.campusphere.net/iap/loginSuccess?sessionToken=0261b15cf2c2469ea0add9f3d66b93b8&ticket=ST-319342-z7T015jSvrKW2JpSYImz1607223617358-Wkwf-cas",
            'host': 'hainanu.campusphere.net'
        }

    @staticmethod
    def GetLoginUrl():  # 获取登陆链接
        apis = {}
        ids = 'ec061503-d0fa-4bbd-9a22-e5eaaccc69e9'
        params = {'ids': ids}
        r = requests.get('https://www.cpdaily.com/v6/config/guest/tenant/info', params=params)

        old_acw_tc = requests.utils.dict_from_cookiejar(r.cookies)['acw_tc']
        apis['old_acw_tc'] = old_acw_tc
        data = r.json()['data'][0]
        appid = data['appId']
        ampUrl = data['ampUrl']

        if 'campusphere' in ampUrl or 'cpdaily' in ampUrl:
            parse = urlparse(ampUrl)
            apis['host'] = parse.netloc
            res = requests.get(parse.scheme + '://' + parse.netloc, allow_redirects=False)
            acw_tc = requests.utils.dict_from_cookiejar(res.cookies)['acw_tc']
            apis['acw_tc'] = acw_tc

            header = {'Cookie': 'acw_tc=' + acw_tc}
            apis['acw_url'] = parse.scheme + '://' + parse.netloc + '/portal/login'
            res = requests.get(apis['acw_url'], headers=header)
            apis['login-url'] = res.url
            apis['data'] = {'appid': appid, 'login_type': 'mobileLogin'}

        ampUrl2 = data['ampUrl2']
        if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
            parse = urlparse(ampUrl2)
            apis['host'] = parse.netloc
            res = requests.get(parse.scheme + '://' + parse.netloc, allow_redirects=False)
            acw_tc = requests.utils.dict_from_cookiejar(res.cookies)['acw_tc']
            apis['acw_tc'] = acw_tc

            header = {'Cookie': 'acw_tc=' + acw_tc}
            apis['acw_url'] = parse.scheme + '://' + parse.netloc + '/portal/login'
            res = requests.get(apis['acw_url'], headers=header)
            apis['login-url'] = res.url
            apis['data'] = {'appid': appid, 'login_type': 'mobileLogin'}
        return apis

    @staticmethod
    def login(apis, account) -> dict or bool:
        url = apis['login-url']

        r = requests.get(url)

        cookie = requests.utils.dict_from_cookiejar(r.cookies)
        JSESSIONID = cookie['JSESSIONID']
        route = cookie['route']

        cookie = 'route=' + route + '; JSESSIONID=' + JSESSIONID + '; org.springframework.web.servlet.i18n' \
                                                                   '.CookieLocaleResolver.LOCALE=zh_CN '
        header = {'Cookie': cookie}

        r = requests.post(url, headers=header)
        lt = re.findall('name="lt" value="(.*)"', r.text)[0]
        key = re.findall('id="pwdDefaultEncryptSalt" value="(.*?)"', r.text)[0]
        dllt = re.findall('name="dllt" value="(.*)"', r.text)[0]
        execution = re.findall('name="execution" value="(.*?)"', r.text)[0]
        rmShown = re.findall('name="rmShown" value="(.*?)"', r.text)[0]

        header = {
            'Cookie': cookie
        }
        pwd = HainanUniversity.AESEncrypt(account['password'], key)
        data = {
            'username': account['username'],
            'password': pwd,
            'lt': lt,
            'dllt': dllt,
            'execution': execution,
            '_eventId': 'submit',
            'rmShown': rmShown
        }
        key = {}

        r = requests.post(url, headers=header, data=data, allow_redirects=0)
        response_headers = r.headers
        Location = response_headers['Location']
        key.update(requests.utils.dict_from_cookiejar(r.cookies))

        res = requests.get(url=Location)
        for i in res.history:
            i: requests.Request
            key.update(requests.utils.dict_from_cookiejar(i.cookies))
        return key

    def get_session(self, account) -> dict or bool:
        apis = self.GetLoginUrl()

        try:
            key = self.login(apis, account)
            headers = {
                "extension": "1",
                "Cpdaily-Extension": self.DESEncrypt(self.user_info['username']),
                "Cookie": 'acw_tc=' + key['acw_tc'] + '; MOD_AUTH_CAS=' + key['MOD_AUTH_CAS'],
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "ARAI.DM"
            }
            return headers
        except KeyError:
            logger.debug(f'[FAILED]登录失败 -- {self.user_info["username"]} || 该用户账号信息过时或需要二步验证')
        except IndexError:
            logger.debug(f'[FAILED]登录失败 -- {self.user_info["username"]} || 本机IP或被冻结 请及时启用GoActions')
            raise requests.exceptions.ProxyError

    @staticmethod
    def DESEncrypt(userID, secret_key='ST83=@XV'):
        iv = [1, 2, 3, 4, 5, 6, 7, 8]

        def encode(s):
            k = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
            s_encrypt = k.encrypt(s, padmode=PAD_PKCS5)
            return bytes.decode(base64.b64encode(s_encrypt))

        Extension = '{"systemName":"android",' \
                    '"systemVersion":"n.m.s",' \
                    '"model":"fucker",' \
                    '"deviceId":"' + str(uuid.uuid1()) + '",' \
                                                         '"appVersion":"8.2.10",' \
                                                         '"lon":' + '110.33493' + ',' \
                                                                                  '"lat":' + '20.063253' \
                    + ',' \
                      '"userId":"' + userID + '"}'
        return encode(Extension)

    def get_unsigned_tasks(self, headers) -> dict or bool:
        res = requests.post(url=self.get_data_url, data=json.dumps({}), headers=headers, timeout=10)
        try:
            latestTask = res.json()['datas']['unSignedTasks'][0]
            return {
                'signInstanceWid': latestTask['signInstanceWid'],
                'signWid': latestTask['signWid']
            }
        except IndexError:
            return False
        except Exception as e:
            logger.exception(e)

    def fill_form(self, params, headers) -> str and dict:
        data = {
            "signInstanceWid": params['signInstanceWid'],
            "signWid": params['signWid']
        }
        res = requests.post(url=self.detial_url, data=json.dumps(data), headers=headers, timeout=10)
        ticks = res.json()['datas']["extraField"][0]["extraFieldItems"]
        for i in ticks:
            if "以下" in i["content"]:
                return i["wid"], res.json()['datas']

    def submit_task(self, params, extraFieldItemWid, headers) -> str or bool:
        data = {
            "signInstanceWid": str(params['signInstanceWid']),
            "longitude": 110.336933,
            "latitude": 20.06208,
            "isMalposition": 0,
            "abnormalReason": "",
            "signPhotoUrl": "",
            "position": "中国海南省海口市美兰区椰风中路",
            "isNeedExtra": "1",
            "extraFieldItems": [{
                "extraFieldItemValue": "37.2℃及以下",
                "extraFieldItemWid": str(extraFieldItemWid)
            }]
        }
        res = requests.post(url=self.signurl, headers=headers, data=json.dumps(data),
                            timeout=100)
        res.encoding = res.apparent_encoding
        if "SUCCESS" in res.text:
            return 'success'
        elif "任务未开始" in res.json().get("message"):
            return 'empty'

    def run(self, user: dict = None) -> bool:
        """

        :param user:
        :return:
        """
        # 加载握手密钥
        self.user_info = user

        try:
            # (√ A++Decoupling) session -- Simulated login the AASoHainanU
            headers = self.get_session(user)

            if headers:

                params = self.get_unsigned_tasks(headers)

                # (√) params success -- get the secret_key-des file of sign-in information
                if params:

                    # (√) task -- sign in tasks(but only one)
                    task, response = self.fill_form(params, headers)

                    # (*)stu_info -- extract private information of students
                    HainanUniversity.private_extract(response, user)

                    # (√) message -- API response json data
                    message = self.submit_task(params, task, headers)

                    # message success -- (model output):task over!send notification SMS
                    # TODO：Function Add: WeChat Push by <Server Kishida>
                    if message == 'success':
                        logger.success(f'[SUCCESS] 签到成功 -- {user["username"]}')

                        # 发送消息通知
                        send_email(
                            msg=f'[{str(datetime.now(TIME_ZONE_CN)).split(".")[0]}]自动签到成功<From.{SECRET_NAME}>',
                            to=user["email"],
                        )

                    # 任务失败 可能原因为：该实体本阶段签到任务已完成
                    elif message == 'empty':
                        logger.info(f'[IGNORE] 签到失败 -- {user["username"]} || 该用户本阶段签到任务已完成')

                # params error -- 任务失败 可能原因为：该实体所在学院下一阶段任务不存在（仅晚签）
                else:
                    logger.info(f'[IGNORE] 签到失败 -- {user["username"]} || 该用户所在学院下一阶段任务不存在')

        # 接收主动抛出的错误：可能原因为 操作过热 IP被封禁
        except requests.exceptions.ProxyError:
            return False

        # 捕获未知异常
        except Exception as e:
            logger.debug(f"[ERROR] 签到异常 -- {user['username']} || 该用户签到任务出现未知异常")
            logger.exception(e)
