from src.BusinessCentralLayer.middleware.flow_io import sync_user_data
from src.BusinessLogicLayer.apis.manager_screenshot import capture_and_upload_screenshot
from src.BusinessLogicLayer.apis.manager_users import stu_twqd, check_display_state


def _select_user_table(username) -> dict or bool:
    """
    同步用户表
    :param username:
    :return:
    """
    # 若用户在库，返回用户密码，否则返回false bool
    for sud in sync_user_data():
        if username == sud['username'] and sud['password']:
            break
    else:
        return False
    return {'password': sud['password']}


def apis_stu_twqd(user: dict):
    user_ = {'username': user.get('username'), }

    # 启动节点任务,该操作为风险操作，权限越界，无需知道用户密码也可完成操作
    return stu_twqd(user_)


def apis_stu_twqd2(user: dict):
    """
    当OSS没有截图时使用此接口
    既已知OSS没有截图，故无论osh-slaver如何执行，都要调用 osh-s上传截图
    :param user:
    :return:
    """

    user_ = {'username': user.get('username'), }

    # 用户鉴权
    ttp = _select_user_table(user_["username"])
    if ttp:
        user_.update(ttp)
    else:
        return {'msg': 'failed', 'info': '用户权限不足', 'code': 101}

    # 使用osh-runner判断用户是否签到
    # 若未签到，startup osh-core 进行签到；
    # 若已签到，kill the osh-core 结束子程序
    stu_state: dict = check_display_state(user_)
    if stu_state['code'] != 902:
        return stu_twqd(user_)

    # 启动Selenium上传截图 并返回调试数据
    return capture_and_upload_screenshot(user_)
