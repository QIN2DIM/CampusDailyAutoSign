__all__ = ['deploy']


def deploy(task_name, upload_snp=None):
    """
    Linux 云端部署
    :param upload_snp:
    :param task_name: CampusDailySpeedupPlus(core()).run
    :return:
    """
    import time
    import schedule
    from datetime import datetime
    from config import TIME_ZONE_CN, MANAGER_EMAIL, logger
    from BusinessCentralLayer.sentinel.noticer import send_email

    schedule.every().day.at("12:00").do(task_name)
    if upload_snp:
        schedule.every().day.at("12:03").do(upload_snp)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.exception(e)
        now_ = str(datetime.now(TIME_ZONE_CN)).split('.')[0]
        send_email(f'{now_} || {e}', to=MANAGER_EMAIL)
