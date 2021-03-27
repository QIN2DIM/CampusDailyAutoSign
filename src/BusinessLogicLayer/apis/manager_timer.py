"""定时任务全局接口"""
__all__ = ['time_container']

from gevent import monkey

monkey.patch_all()
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from src.BusinessCentralLayer.middleware.flow_io import sync_user_data
from src.BusinessLogicLayer.apis.vulcan_ash import SignInSpeedup, SignInWithScreenshot
from src.BusinessLogicLayer.apis.manager_cookie import check_admin_cookie
from src.BusinessCentralLayer.setting import logger, ENABLE_UPLOAD, TIMER_SETTING, config_
from src.BusinessLogicLayer.plugins.noticer import send_email


def _offload_group_users() -> list:
    if not all(config_['group']):
        return []
    group_ = set(config_['group'])
    group_ = [{'username': j} for j in group_]
    # 检测管理员权限时效性并刷新全局cookie
    check_admin_cookie()
    # 此处的协程功率不宜超过2，教务官网可能使用了并发限制，有IP封禁风险
    SignInSpeedup(task_docker=group_).interface()


def _release_task_cache():
    from src.BusinessCentralLayer.setting import SERVER_DIR_CACHE_FOR_TIMER
    logger.info(f"<TimeContainer> Clean up cache garbage...")

    if os.path.exists(SERVER_DIR_CACHE_FOR_TIMER):
        cache_files = os.listdir(SERVER_DIR_CACHE_FOR_TIMER)
        if cache_files.__len__() > 0:
            for cache_ in cache_files:
                try:
                    os.remove(os.path.join(SERVER_DIR_CACHE_FOR_TIMER, cache_))
                except Exception as e:
                    logger.error(f"<TimeContainer> Cache cleaning exception | {e} | {cache_}")


def _task_handle(kernel: str = None):
    """

    :param kernel: plus： 截图上传模式   general 普通打卡
    :return:
    """
    logger.info(f"<TimeContainer> Startup TimeContainer Kernel! ")
    # -----------------------------
    # 参数重组
    # -----------------------------
    if kernel is None:
        kernel = ENABLE_UPLOAD
    # -----------------------------
    # 拉取临时组用户并刷新cookie
    # -----------------------------
    _offload_group_users()
    # -----------------------------
    # 根据全局yaml确定任务内核并执行任务
    # -----------------------------
    task_kernel = 'plus' if kernel else 'general'
    if task_kernel == 'general':
        SignInSpeedup(task_docker=sync_user_data(), power=os.cpu_count()).interface()
    elif task_kernel == 'plus':
        SignInWithScreenshot(task_docker=sync_user_data(), power=os.cpu_count()).interface()
    # -----------------------------
    # 回收任务缓存
    # -----------------------------
    _release_task_cache()
    # -----------------------------
    # TODO 订阅发布
    # -----------------------------
    send_email(
        msg=f"<TimeContainer> 用户签到任务（{task_kernel}）已完成",
        to_='self'
    )


def time_container():
    _core = BlockingScheduler()

    logger.success(f'<TimeContainer> || 部署定时任务 || {_core.__class__.__name__}')

    # 测试配置
    # _core.add_job(func=_timed_sign_in, trigger='interval', seconds=10)

    # 添加任务
    _core.add_job(
        func=_task_handle,
        trigger='cron',
        hour=TIMER_SETTING['hour'],
        minute=TIMER_SETTING['minute'],
        second=TIMER_SETTING['second'],
        jitter=TIMER_SETTING['jitter'],
        timezone=TIMER_SETTING['tz_']
    )

    # TODO 添加功能——任务动态添加
    #  1. 支持通过外部接口添加账户进行定时签到
    #  2. 添加每日漏检扫描功能，对“在库”用户的签到状态进行扫描，对漏检的执行签到
    _core.start()


if __name__ == '__main__':
    _task_handle()
