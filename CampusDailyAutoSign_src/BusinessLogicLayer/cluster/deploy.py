__all__ = ['deploy']


def deploy(task_name, tz='cn'):
    """
        Linux 云端部署
    :param task_name: CampusDailySpeedUp(HainanUniversity).run
    :param tz:
    :return:
    """
    import time
    import schedule
    from datetime import datetime, timedelta
    from config import TIME_ZONE_CN, MANAGER_EMAIL, logger
    from BusinessCentralLayer.sentinel.noticer import send_email

    # todo:植入截图合成脚本
    morn, noon, night = "07:30", "12:00", "21:00"

    if tz == 'us':
        # 纽约时区
        morn = (datetime(2020, 11, 6, 7, 0, 0) - timedelta(hours=13)).strftime("%H:%M")
        noon = (datetime(2020, 11, 6, 12, 0, 0) - timedelta(hours=13)).strftime("%H:%M")
        night = (datetime(2020, 11, 6, 21, 0, 0) - timedelta(hours=13)).strftime("%H:%M")

    schedule.every().day.at(morn).do(task_name)
    schedule.every().day.at(noon).do(task_name)
    schedule.every().day.at(night).do(task_name)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.exception(e)
        now_ = str(datetime.now(TIME_ZONE_CN)).split('.')[0]
        send_email(f'{now_} || {e}', to=MANAGER_EMAIL)
