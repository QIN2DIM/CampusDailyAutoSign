import sys

import pytz
from loguru import logger

from src.config import *

# ------------------------------
# 系统文件路径
# ------------------------------
"""
--ROOT
    --bin
    --docs
    --src
        --layers...
        --logs
        --database
        --config.yaml
        --config-sample.yaml
        --config.py
    --main.py
    --requirements.txt
"""
# src
SERVER_DIR_PROJECT = os.path.dirname(os.path.dirname(__file__))
# src/database
SERVER_DIR_DATABASE = os.path.join(SERVER_DIR_PROJECT, 'Database')
# src/database/stu_info
SERVER_DIR_CACHE = os.path.join(SERVER_DIR_DATABASE, 'stu_info')
# src/database/stu_screenshot
SERVER_DIR_SCREENSHOT = os.path.join(SERVER_DIR_DATABASE, 'stu_screenshot')
# src/database/cache
SERVER_DIR_CACHE_FOR_TIMER = os.path.join(SERVER_DIR_DATABASE, 'cache')
# src/database/superuser_cookies.txt
SERVER_PATH_COOKIES = os.path.join(SERVER_DIR_DATABASE, 'superuser_cookies.txt')
#
if "win" in sys.platform:
    CHROMEDRIVER_PATH = SERVER_DIR_PROJECT + "/BusinessLogicLayer/plugins/chromedriver.exe"
else:
    CHROMEDRIVER_PATH = SERVER_DIR_PROJECT + "/BusinessLogicLayer/plugins/chromedriver"
# ------------------------------
# 业务层日志配置
# ------------------------------
# src/logs
SERVER_DIR_LOG = os.path.join(SERVER_DIR_PROJECT, "logs")
# src/logs/runtime.log
logger.add(
    os.path.join(SERVER_DIR_LOG, 'runtime.log'),
    level='INFO',
    rotation='1 week',
    retention='20 days',
)
logger.add(
    os.path.join(SERVER_DIR_LOG, 'error.log'),
    level='ERROR',
    rotation='1 week'
)

# ------------------------------
# 脚本全局参数
# ------------------------------

# 时区校准--BeijingTimeZone
TIME_ZONE_CN = pytz.timezone('Asia/Shanghai')

# ------------------------------
# public flask API
# ------------------------------
# 体温签到 --General模式
PUBLIC_API_STU_TWQD = "/cpds/api/stu_twqd"

# 体温签到 -- UploadSnp模式 | 向General兼容，并对在库用户具备截图上传（更新）能力
PUBLIC_API_STU_TWQD2 = "/cpds/api/stu_twqd2"

# 项目tos声明
PUBLIC_API_TOS = "/cpdaily/api/item/tos"

# 项目重定向首页
PUBLIC_API_REDIRECT = "/"

# ------------------------------
# response status code by system
# ------------------------------

OSH_STATUS_CODE = {
    # 应立即结束任务
    900: '任务劫持。该用户今日签到数据已在库',
    901: '任务待提交。今日签到任务已出现，但未抵达签到开始时间。',

    # 应直接在当前列表调用截图上传模块
    902: 'The task has been submitted. The task status shows that the user has checked in.',

    # 调用主程序完成签到任务
    903: '任务待提交。任务出现并抵达开始签到时间。',
    904: '',

    # 任务句柄
    300: 'The task was submitted successfully. Sign in successfully through RUshRunner.',
    301: 'The task submission failed. An unknown error occurred.',
    302: '任务提交失败。重试次数超过阈值',
    303: '任务提交失败。Selenium操作超时',
    304: 'The task submission failed. The user does not use the network service lobby to sign in.'
         ' The specific performance is that all check-in tasks within the date range are empty.',
    305: '任务提交失败。T_STU_TEMP_REPORT_MODIFY 返回值为0。',

    306: '任务解析异常。Response解析json时抛出的JSONDecodeError错误，根本原因为返回的datas为空。可能原因为：接口变动，网络超时，接口参数变动等。',
    310: '任务重置成功。使用OshRunner越权操作，重置当前签到状态。',

    400: "The superuser's cookie is refreshed successfully.",
    401: 'Login failed. Admin Cookie stale! Super User Cookie expired/error/file not in the target path.',
    402: '登录失败。OSH_IP 可能或被封禁，也可能是该用户不适用本系统（既没有任何在列任务）',
    403: '更新失败。MOD_AMP_AUTH获取异常，可能原因为登陆成功但未获取关键包',

    500: 'The screenshot was uploaded successfully.',
    501: '体温截图获取失败。可能原因为上传环节异常或登录超时（账号有误，操作超时）'
}

if __name__ == '__main__':
    print(f'>>> 读取配置文件{config_}')
