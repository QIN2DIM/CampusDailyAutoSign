__all__ = ['reload_admin_cookie', 'quick_refresh_cookie', 'check_admin_cookie']

from typing import Tuple

from src.BusinessCentralLayer.setting import SUPERUSER, logger, SERVER_PATH_COOKIES
from src.BusinessLogicLayer.cluster.osh_core import osh_core


def reload_admin_cookie(user=None) -> Tuple[int, str]:
    """
    Obtain user cookies through Selenium
    :param user: When no parameters are passed in, update the cookie for the superuser
    :return: status code(int) and cookie(str)
    """
    if user is None:
        user = SUPERUSER
        kernel = 'admin'
    else:
        kernel = 'general'
    return osh_core(silence=True, anti=False).rush_cookie_pool(user=user, kernel=kernel)


def quick_refresh_cookie(user: dict = None) -> str:
    """
    Obtain user cookies through ‘Requests POST’
    :param user: username and password
    :return: cookie(str)
    """
    from src.BusinessLogicLayer.cluster.osh_runner import runner
    return runner.quick_refresh_cookie(user=user)


def check_admin_cookie():
    """
    Check the timeliness of the cookie, and automatically pull the cookie if the cookie fails
    :return:
    """
    from src.BusinessLogicLayer.cluster.osh_runner import runner

    # Load superuser's cookie
    with open(SERVER_PATH_COOKIES, 'r', encoding='utf8') as f:
        cookie = f.read().strip()

    # Judging cookie timeliness
    is_available = runner.check_cookie(mod_amp_auth=cookie)
    logger.info(f"<CookieManager> The status of superuser's cookie is :{is_available}")\

    # If the cookie fails, call the relevant module to update the cookie
    if not is_available:
        logger.debug("<CookieManager> Try to reload superuser's cookie.")
        reload_admin_cookie()


if __name__ == '__main__':
    check_admin_cookie()
