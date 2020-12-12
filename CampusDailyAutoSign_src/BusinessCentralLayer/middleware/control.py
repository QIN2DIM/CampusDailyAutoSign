__all__ = ['Interface']

# FIXME 如果您在本目录下直接运行，或处于开发者调试模式，请将此行`exec`注释掉
exec('from gevent import monkey\nmonkey.patch_all()')

import csv
import multiprocessing
import os

from BusinessCentralLayer.middleware.coroutine_engine import CampusDailySpeedUp
from BusinessLogicLayer.cluster.deploy import deploy
from BusinessLogicLayer.cluster.slavers.hainanu import HainanUniversity
from BusinessLogicLayer.cluster.slavers.local_actions import NoCloudAction
from BusinessViewLayer.myapp.forms import app
from config import *

if 'win' in sys.platform:
    multiprocessing.freeze_support()

# 解决方案
__core__ = {
    'hainanu': HainanUniversity(),
    'local': NoCloudAction()
}

# 加速策略
__speed_up_way__ = CampusDailySpeedUp


class SystemEngine(object):
    def __init__(self, **kwargs):
        """

        @param kwargs:
        """
        # 读取配置文件路径
        self.config_path = SERVER_PATH_CONFIG_USER
        logger.info('<定位配置>:config_path')

        # 核心装载，任务识别
        self.core = __core__['hainanu'] if kwargs.get(
            "core") is None else kwargs.get("core")
        logger.info("<驱动核心>:core:{}".format(self.core.__class__.__name__))

        # 加速策略挂载
        self.speed_up_way = __speed_up_way__ if kwargs.get(
            "speed_up_way") is None else kwargs.get("speed_up_way")
        logger.info("<加速策略>:speed_up_way:<{}>".format(
            self.speed_up_way.__module__))

        # 默认linux下自动部署
        self.enable_deploy = ENABLE_DEPLOY if kwargs.get(
            "enable_deploy") is None else kwargs.get("enable_deploy")
        logger.info('<部署设置>:deploy:{}'.format(self.enable_deploy))

        # 单机协程加速配置
        self.speed_up = ENABLE_COROUTINE if kwargs.get(
            "speed_up") is None else kwargs.get("speed_up")
        logger.info("<协程加速>:speed_up:{}".format(self.speed_up))

        # 初始化进程
        self.deploy_process, self.server_process = None, None
        logger.info('<初始化进程>:deploy_process:server_process')

    def __test__(self):

        # 调用协程控制器
        signal_server = self.speed_up_way(
            core=self.core, config_path=self.config_path)
        logger.debug('<单机运行>工程核心准备就绪 任务即将开始')
        signal_server.run(speed_up=self.speed_up)
        logger.success('<单机运行>任务结束')

    def run_deploy(self):
        deploy(self.speed_up_way(core=self.core, config_path=self.config_path).run)

    @staticmethod
    def run_server():
        app.run(host='0.0.0.0', port=API_PORT,
                debug=API_DEBUG, threaded=API_THREADED)

    def run(self):
        try:
            logger.debug('<Gevent>工程核心准备就绪 任务即将开始')
            if self.enable_deploy:
                self.deploy_process = multiprocessing.Process(
                    target=self.run_deploy, name='定时签到')
                logger.info(
                    f'starting {self.deploy_process.name}, pid {self.deploy_process.pid}...')
                self.deploy_process.start()

            if ENABLE_SERVER:
                self.server_process = multiprocessing.Process(
                    target=self.run_server, name='程序接口')
                logger.info(
                    f'starting {self.server_process.name}, pid {self.server_process.pid}...')
                self.server_process.start()

            self.deploy_process.join()
            self.server_process.join()
        except TypeError or AttributeError as e:
            logger.exception(e)
        except KeyboardInterrupt:
            logger.debug('received keyboard interrupt signal')
            self.server_process.terminate()
            self.deploy_process.terminate()
        finally:
            self.deploy_process.join()
            self.server_process.join()
            logger.info(
                f'{self.deploy_process.name} is {"alive" if self.deploy_process.is_alive() else "dead"}')
            logger.info(
                f'{self.server_process.name} is {"alive" if self.server_process.is_alive() else "dead"}')
            logger.success('<Gevent>任务结束')


class PrepareEnv(object):
    def __init__(self):
        """
        //ROOT
        --BCL 中枢层
        --BLL 逻辑层
        --BVL 交互层
        --DATABASE
            --logs
            --stu_info
            --config_user.csv
        """
        ROOT = [
            SERVER_PATH_CACHE,
        ]

        if os.path.split(SERVER_PATH_CONFIG_USER)[-1] not in os.listdir(SERVER_DIR_DATABASE):
            logger.warning(f"检测到您初次运行{SECRET_NAME}，我们将为您重构文档树，"
                           f"请在重构结束后配置任务队列，并重启任务")
            exec("from time import sleep\nsleep(1)")
            for dir_ in ROOT:
                if os.path.split(dir_)[-1] not in os.listdir(SERVER_DIR_DATABASE):
                    logger.info(f'正在拉取文件 -- {dir_}')
                    os.mkdir(dir_)

            logger.info(f'正在拉取文件 -- {SERVER_PATH_CONFIG_USER}')
            with open(SERVER_PATH_CONFIG_USER, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(TITLE)
                writer.writerow(TEST_INFO)
            logger.success('<环境部署>任务结束')
            exit()
            # logger.success('用户表初始化成功 任务即将重启')
            # logger.info('任务已重启 开始检查部署环境')

        with open(SERVER_PATH_CONFIG_USER, 'r', encoding='utf-8', newline='') as f:
            if TEST_INFO in [i for i in csv.reader(f) if i]:
                logger.debug('任务队列为空 请根据参考案例手动添加第一条测试数据 并移除测试数据(第二行)')
                logger.info(f"数据表地址 {SERVER_PATH_CONFIG_USER}")
                exit()


PrepareEnv()


class Interface(object):

    @staticmethod
    def __deploy__(core, speed_up_way, speed_up):
        SystemEngine(enable_deploy=True, speed_up=speed_up,
                     core=core, speed_up_way=speed_up_way).run()

    @staticmethod
    def __check__(speed_up):
        SystemEngine(speed_up=speed_up).__test__()

    @staticmethod
    def run(deploy_: bool = None, coroutine_speed_up: bool = True, core=None, speed_up_way=None):
        """
        程序入口
        @param deploy_:
            1. ‘check’:单机运行<wins or mac 默认>  ‘deploy’:服务器部署<linux下默认>
            2. 若在服务器上运行请使用’deploy‘模式--部署定时任务
        @param coroutine_speed_up: 开启协程加速，在linux下默认开启
        @param core: 驱动核心，默认海南大学
        @param speed_up_way: 加速策略，默认协程加速
        @return:
        """
        if deploy_ is None:
            deploy_ = True if 'linux' in sys.platform else False
        if deploy_:
            Interface.__deploy__(core, speed_up_way, coroutine_speed_up)
        else:
            Interface.__check__(coroutine_speed_up)
