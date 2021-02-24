# coding=utf-8
import os
import shutil

import yaml

# ---------------------------------------------------
# TODO 配置文件索引
# 默认的单机配置文件为 config.yaml
# ---------------------------------------------------

# 若在单机上开启多个进程的任务，既每个进程应对应一个启动配置文件（.yaml）则需改动此处user_指向的文件名，如：
# config_1.yaml   user_= os.path.join(os.path.dirname(__file__), 'config_1.yaml')
# config_master.yaml   user_= os.path.join(os.path.dirname(__file__), 'config_master.yaml')
_config_yaml_: str = os.path.join(os.path.dirname(__file__), 'config.yaml')

# 配置模板的文件名 无特殊需求请不要改动
_sample_yaml_: str = os.path.join(os.path.dirname(__file__), 'config-sample.yaml')

try:
    if not os.path.exists(_sample_yaml_):
        print(">>> 请不要删除系统生成的配置模板config-sample.yaml，确保它位于工程根目录下")
        raise FileNotFoundError
    elif os.path.exists(_sample_yaml_) and not os.path.exists(_config_yaml_):
        print(f">>> 工程根目录下缺少config.yaml配置文件")
        shutil.copy(_sample_yaml_, _config_yaml_)
        print(">>> 初始化启动参数... ")
        # print(">>> 请根据docs配置启动参数 https://github.com/QIN2DIM/V2RayCloudSpider")
        exit()
    elif os.path.exists(_sample_yaml_) and os.path.exists(_config_yaml_):
        # 读取yaml配置变量
        with open(_config_yaml_, 'r', encoding='utf8') as stream:
            config_ = yaml.load(stream.read(), Loader=yaml.FullLoader)
            if __name__ == '__main__':
                print(f'>>> 读取配置文件{config_}')
except FileNotFoundError:
    try:
        import requests

        res_ = requests.get("http://123.56.77.6:8888/down/3id6WqndXl8j")
        with open(_sample_yaml_, 'wb') as fp:
            fp.write(res_.content)
        print(">>> 配置模板拉取成功,请重启项目")
    except Exception as e_:
        print(e_)
        print('>>> 配置模板自动拉取失败，请检查本地网络')
    finally:
        exit()

# -----------------------------------------------------------
# TODO (√)ENABLE -- 权限开关
# -----------------------------------------------------------
APP_PERMISSIONS: dict = config_['app-permissions']
ENABLE_SERVER: bool = APP_PERMISSIONS['server']
ENABLE_DEPLOY: bool = APP_PERMISSIONS['deploy']
ENABLE_UPLOAD: bool = APP_PERMISSIONS['sync_snp']

# -----------------------------------------------------------
# TODO (√)SuperUser -- 网上服务大厅账号
# 此项用于刷新cookie pool，若不填写程序将无法正常执行
# -----------------------------------------------------------
SUPERUSER: dict = config_['superuser']

# -----------------------------------------------------------
# TODO (√)AliyunOss -- 对象存储Oss ACKEY
# 此项用于存储体温签到截图，为系统核心数据库，必须设置
# -----------------------------------------------------------
SDK_OSS_SCKEY: dict = config_['sdk-oss-sckey']
# -----------------------------------------------------------
# TODO (√)MySQL_SETTING
# 数据库配置
# -----------------------------------------------------------
MySQL_SETTING: dict = config_['sdk-rds-sckey']

# -----------------------------------------------------------
# TODO (√)SMTP_ACCOUNT -- 用于发送panic信息警报，默认发送给自己
# 推荐使用QQ邮箱，开启邮箱SMTP服务教程如下
# https://service.mail.qq.com/cgi-bin/help?subtype=1&&id=28&&no=1001256
# -----------------------------------------------------------
SMTP_SCKEY: dict = config_['smtp-sckey']

# -----------------------------------------------------------
# (-)MANAGER_EMAIL -- 管理员账号，接收debug邮件
# Default -> 当SMTP开启时自动跟随配置
# -----------------------------------------------------------
MANAGER_EMAIL = set(config_['smtp-managers'])

# -----------------------------------------------------------
# TODO (√) Timer Setting
# 1. 主程序业务定时器，用于设定每日打卡任务的启动时间
# 2. 强制使用cron定时器，每日的XX小时，XX分钟，XX秒启动任务
# 2.1 如hour-minute-second为 12-25-41则表示每天的中午12点25分41！左右！启动任务
# 2.2 设有jitter浮动误差控制，单位为300秒，既在设定日期的jitter浮动时间区间内发起任务
# 2.3 设有tz_时区控制，默认"Asia/Shanghai"
# -----------------------------------------------------------
TIMER_SETTING = config_['timer-setting']

# -----------------------------------------------------------
# TODO (√)API_HOST
# Default -> True
# -----------------------------------------------------------
FLASK_SETTING: dict = config_['flask-setting']
API_HOST: str = FLASK_SETTING['host']
API_PORT: int = FLASK_SETTING['port']
API_DEBUG: bool = FLASK_SETTING['debug']
API_THREADED: bool = FLASK_SETTING['threaded']
API_SLAVES: list = FLASK_SETTING['slaves']

