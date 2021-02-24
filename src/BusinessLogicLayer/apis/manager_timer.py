"""定时任务全局接口"""
__all__ = ['time_container']

from gevent import monkey

monkey.patch_all()
from apscheduler.schedulers.blocking import BlockingScheduler
from src.BusinessCentralLayer.middleware.flow_io import sync_user_data
from src.BusinessLogicLayer.apis.vulcan_ash import SignInSpeedup, SignInWithScreenshot

from src.BusinessCentralLayer.setting import logger, MANAGER_EMAIL, ENABLE_UPLOAD, TIMER_SETTING, config_
from src.BusinessLogicLayer.plugins.noticer import send_email


def _offload_group_users():
    if not all(config_['group']):
        return False
    group_ = set(config_['group'])
    group_ = [{'username': j} for j in group_]

    # 此处的协程功率不易超过2，教务官网可能使用了并发限制，有IP封禁风险
    SignInSpeedup(task_docker=group_).interface()


def _timed_sign():
    """
    定时签到-通用模式，
    :return:
    """

    logger.info(f"<TimeContainer> Run sign General ")

    # 拉取临时组用户
    _offload_group_users()

    SignInSpeedup(task_docker=sync_user_data(), power=2).interface()

    # 邮件通知
    # TODO 发送报表，
    send_email(
        msg="<TimeContainer> 本机签到任务（General）已完成",
        to_='self'
    )


def _timed_sign_and_upload():
    """
    定时签到-截图上传模式，与通用模式无法共存
    :return:
    """

    logger.info(f"<TimeContainer> Run sign Capture&Sign ")

    # 拉取临时组用户
    _offload_group_users()

    SignInWithScreenshot(task_docker=sync_user_data(), power=2).interface()

    send_email(
        msg="<TimeContainer> 用户签到任务（UploadSnp）已完成",
        to_='self'
    )


def time_container():
    _core = BlockingScheduler()

    logger.success(f'<TimeContainer> || 部署定时任务 || {_core.__class__.__name__}')

    # 测试配置
    # _core.add_job(func=_timed_sign_in, trigger='interval', seconds=10)

    # 配置签到任务
    _docker_handle = _timed_sign_and_upload if ENABLE_UPLOAD else _timed_sign

    # 添加任务
    _core.add_job(
        func=_docker_handle,
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
    _offload_group_users()
