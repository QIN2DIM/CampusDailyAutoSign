__all__ = ['sei']

import multiprocessing

from src.BusinessCentralLayer.setting import *
from src.BusinessLogicLayer.plugins.noticer import send_email
from src.BusinessViewLayer.myapp.forms import app

if 'win' in sys.platform:
    multiprocessing.freeze_support()


class _SystemEngine(object):
    def __init__(self):

        # 截图上传权限
        logger.info(f'<SystemEngine> EnableUploadScreenshot || {ENABLE_UPLOAD}')

        # 是否部署定时任务
        logger.info(f'<SystemEngine> EnableTimedTask || {ENABLE_DEPLOY}')

        # 单机协程加速配置
        logger.info(f"<SystemEngine> EnableCoroutine || True(Forced to use)")

        # 初始化进程
        logger.info('<SystemEngine> InitChildProcess')

    @staticmethod
    def run_deploy():
        from src.BusinessLogicLayer.apis.manager_timer import time_container
        time_container()

    @staticmethod
    def run_server():
        app.run(host='0.0.0.0', port=API_PORT, debug=API_DEBUG, threaded=API_THREADED)

    def startup(self):
        process_list = []
        try:
            # 部署<单进程多线程>定时任务
            if ENABLE_DEPLOY:
                process_list.append(multiprocessing.Process(target=self.run_deploy, name='deploymentTimingTask'))

            # 部署flask
            if ENABLE_SERVER:
                process_list.append(multiprocessing.Process(target=self.run_server, name='deploymentFlaskAPI'))

            # 执行多进程任务
            for process_ in process_list:
                logger.success(f'<SystemEngine> Startup -- {process_.name}')
                process_.start()

            # 添加阻塞
            for process_ in process_list:
                process_.join()

            logger.success('<SystemEngine> The core of the project is ready and the task is about to begin.')
        except TypeError or AttributeError as e:
            logger.exception(e)
            send_email(f"<SystemEngine> Program termination || {str(e)}", to_='self')
        except KeyboardInterrupt:
            # FIXME 确保进程间不产生通信的情况下终止
            logger.debug('<SystemEngine> Received keyboard interrupt signal')
            for process_ in process_list:
                process_.terminate()
        finally:
            logger.success('<SystemEngine> End the <CampusDailyAutoSign-NoneBot>')


class _SystemEngineInterface(object):

    @staticmethod
    def startup_system():
        _SystemEngine().startup()


sei = _SystemEngineInterface()
