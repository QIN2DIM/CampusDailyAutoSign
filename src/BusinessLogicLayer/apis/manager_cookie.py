__all__ = ['get_admin_cookie', 'quick_refresh_cookie']

from typing import Tuple

from src.BusinessCentralLayer.setting import SUPERUSER, logger
from src.BusinessLogicLayer.cluster.osh_core import osh_core


def get_admin_cookie(user=None) -> Tuple[int, str]:
    """
    通过模拟登陆的方案获取用户cookie
    :param user: 在不传入参数时，默认为超级用户更新cookie
    :return:
    """
    if user is None:
        user = SUPERUSER
    logger.debug('<CookieManager> Reload Superuser Cookie.')
    return osh_core(silence=True, anti=False).rush_cookie_pool(user)


def quick_refresh_cookie(user: dict = None):
    from src.BusinessLogicLayer.cluster.osh_runner import runner
    return runner.quick_refresh_cookie(user=user)
