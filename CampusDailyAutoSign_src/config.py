# coding=utf-8
import random
import sys
from os.path import dirname, join

import pytz
from environs import Env
from loguru import logger

env = Env()
env.read_env()

"""
=========================== ʕ•ﻌ•ʔ ===================================
    (·▽·)欢迎使用CampusDailyAutoSign，请跟随提示合理配置项目启动参数
=========================== ʕ•ﻌ•ʔ ===================================
"""
# >>> (√) 强制填写；(*)可选项
# -----------------------------------------------------------
# TODO (√)ENABLE -- 权限开关
# -----------------------------------------------------------
ENABLE_SMTP = env.bool("ENABLE_SMTP", True)
ENABLE_SERVER = env.bool("ENABLE_IO", True)
ENABLE_DEPLOY = env.bool("ENABLE_DEPLOY", True if 'linux' in sys.platform else False)
ENABLE_COROUTINE = env.bool("ENABLE_COROUTINE", True if 'linux' in sys.platform else False)
ENABLE_EMAIL = True

# -----------------------------------------------------------
# TODO (√)SuperUser -- 网上服务大厅账号
# 此项用于刷新cookie pool，若不填写程序将无法正常执行
# -----------------------------------------------------------
SUPERUSER = {
    'username': '',
    'password': ''
}
# -----------------------------------------------------------
# TODO (√)AliyunOss -- 对象存储Oss ACKEY
# 此项用于存储体温签到截图，为系统核心数据库，必须设置
# -----------------------------------------------------------

ACKEY = {
    'id': '',
    'secret': '',
    'bucket_name': '',
    'endpoint': ''
}

# -----------------------------------------------------------
# TODO (√)SMTP_ACCOUNT -- 用于发送panic信息警报，默认发送给自己
# 推荐使用QQ邮箱，开启邮箱SMTP服务教程如下
# https://service.mail.qq.com/cgi-bin/help?subtype=1&&id=28&&no=1001256
# -----------------------------------------------------------
SMTP_ACCOUNT: dict = env.dict(
    "SMTP_ACCOUNT",
    {
        'email': '',  # SMTP邮箱
        'sid': '',  # SMTP授权码
    }
)

# -----------------------------------------------------------
# (-)MANAGER_EMAIL -- 管理员账号，接收debug邮件
# Default -> 当SMTP开启时自动跟随配置
# -----------------------------------------------------------
MANAGER_EMAIL = env.str("MANAGER_EMAIL", SMTP_ACCOUNT['email'])

# -----------------------------------------------------------
# TODO (√)API_HOST -- 服务器IP
# Default -> True
# -----------------------------------------------------------
API_HOST: str = env.str("API_HOST", '')
API_PORT: int = env.int("API_PORT", 6577)
API_DEBUG: bool = env.bool("API_DEBUG", False)
API_THREADED: bool = env.bool("API_THREADED", True)
# -----------------------------------------------------------
# (*)DATABASE -- 数据库设置
# Default -> False 默认使用文件型数据库
# -----------------------------------------------------------
MYSQL_HOST = env.str("DATABASE_HOST", 'localhost')
MYSQL_PORT = env.int("MYSQL_PORT", 3306)
MYSQL_PASSWORD = env.str("MYSQL_PASSWORD", "")
MYSQL_DB = env.str("MYSQL_DB", "cpds_db")

"""
=========================== ʕ•ﻌ•ʔ ===================================
如果您并非<CampusDailyAutoSign>项目开发者 请勿修改以下变量的默认参数
=========================== ʕ•ﻌ•ʔ ===================================

                                    Enjoy it -> ♂main.py
"""

# ------------------------------
# 用户组全局变量
# ------------------------------

LONGITUDE: str = env.str("LONGITUDE", f'{round(random.uniform(110.331974, 110.339974), 6)}')
LATITUDE: str = env.str("LATITUDE", f'{round(random.uniform(20.061120, 20.066120), 6)}')
SCHOOL: str = env.str("SCHOOL", '海南大学')
ADDRESS: str = env.str("ADDRESS", '中国海南省海口市美兰区云翮南路')
ABNORMAL_REASON = None
QnA = env.dict(
    "QnA",
    {
        '早晨您的体温是': '37.2℃及以下',
        '您中午的体温是': '37.2℃及以下',
        '晚上您的体温是': '37.2℃及以下',
    }
)

# ------------------------------
# 系统文件路径
# ------------------------------
SERVER_DIR_PROJECT = env.str("SERVER_DIR_PROJECT", dirname(__file__))
SERVER_DIR_DATABASE = env.str("SERVER_DIR_DATABASE", join(SERVER_DIR_PROJECT, 'Database'))
SERVER_DIR_FLASK = env.str("SERVER_DIR_FLASK", join(SERVER_DIR_PROJECT, 'BusinessViewLayer'))
SERVER_PATH_CONFIG_USER = env.str("SERVER_PATH_CONFIG_USER", join(SERVER_DIR_DATABASE, 'config_user.csv'))
SERVER_DIR_CACHE = env.str("SERVER_PATH_CACHE", join(SERVER_DIR_DATABASE, 'stu_info'))
SERVER_DIR_SCREENSHOT = join(SERVER_DIR_DATABASE, 'stu_screenshot')
SERVER_PATH_COOKIES = join(SERVER_DIR_DATABASE, 'superuser_cookies.txt')
if "win" in sys.platform:
    CHROMEDRIVER_PATH = dirname(__file__) + "/BusinessCentralLayer/chromedriver.exe"
else:
    CHROMEDRIVER_PATH = dirname(__file__) + "/BusinessCentralLayer/chromedriver"
# 业务层日志路径
SERVER_DIR_LOG = env.str("SERVER_DIR_LOG", join(SERVER_DIR_DATABASE, "logs"))
logger.add(env.str('LOG_RUNTIME_FILE', join(SERVER_DIR_LOG, 'runtime.log')), level='DEBUG', rotation='1 week',
           retention='20 days', )
logger.add(env.str('LOG_ERROR_FILE', join(SERVER_DIR_LOG, 'error.log')), level='ERROR', rotation='1 week')

# 哨兵脚本
FLASK_PATH_FORMS = env.str("FLASK_PATH_FORMS", join(SERVER_DIR_FLASK, 'forms.py'))

# ------------------------------
# 脚本全局参数
# ------------------------------

SECRET_NAME: str = env.str("SECRET_NAME", 'CampusDailyAutoSign')

# 消息验证模式
DEBUG: bool = env.bool("DEBUG", False)

# 时区校准--BeijingTimeZone
TIME_ZONE_CN = pytz.timezone('Asia/Shanghai')
TIME_ZONE_US = pytz.timezone('America/New_York')

# 信息键
TITLE: list = env.list("TITLE", ['school', 'username', 'password', 'email'])
TEST_INFO = ['海南大学', '20181234123400', '110qwe.zeq12+', 'ARAI.DM@hainanu.edu.cn']
# ------------------------------
# 路由接口
# ------------------------------
ROUTE_API: dict = env.dict(
    "ROUTE_API",
    {
        'my_blog': '/',  # 若用户访问原生IP则重定向

        'tos': '/cpdaily/api/item/tos',  # 服务条款

        'quick_start': '/cpdaily/api/item/quick_start',  # 业务解耦-快速注册

        'verity_account_exist': '/cpdaily/api/item/verity_account_exist',  # 业务分离-验证该用户是否已在本项目数据库

        'verity_cpdaily_account': '/cpdaily/api/item/verity_cpdaily_account',  # 业务分离-验证今日校园账号（学号+密码）是否正确

        'verity_email_passable': '/cpdaily/api/item/verity_email_passable',  # 业务分离-验证邮箱格式是否合法

        'send_verity_code': '/hainanu/api/item/send_verify_code',  # 业务分离-发送验证码

        'add_user': '/cpdaily/api/item/add_user',  # 业务分离-数据入库

    }
)
