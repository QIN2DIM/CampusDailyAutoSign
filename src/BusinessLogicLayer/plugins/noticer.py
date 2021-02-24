__all__ = ['send_email']

import smtplib
from email.header import Header
from email.mime.text import MIMEText
from typing import List

from src.BusinessCentralLayer.setting import SMTP_SCKEY, logger


def send_email(msg: str, to_: List[str] or str or set, headers: str = None):
    """
    发送运维信息，该函数仅用于发送简单文本信息
    :param msg: 正文内容
    :param to_: 发送对象
                1. str
                    to_ == 'self'，发送给“自己”
                2. List[str]
                    传入邮箱列表，群发邮件（内容相同）。
    :param headers:
    :return: 默认为'<V2Ray云彩姬>运维日志'
    """
    headers = headers if headers else '<CampusDailyAutoSign>运维日志'
    sender = SMTP_SCKEY.get('email')
    password = SMTP_SCKEY.get('sid')
    smtp_server = 'smtp.qq.com'
    message = MIMEText(msg, 'plain', 'utf-8')
    message['From'] = Header('ARAI.DM', 'utf-8')  # 发送者
    message['Subject'] = Header(f"{headers}", 'utf-8')
    server = smtplib.SMTP_SSL(smtp_server, 465)

    # ---------------------------------------
    # 输入转换
    # ---------------------------------------

    # 处理单个传递对象
    if isinstance(to_, str):
        # 自发邮件
        if to_ == 'self':
            to_ = [sender, ]
        else:
            to_ = [to_, ]

    # 处理多个传递对象
    if isinstance(to_, list):
        # 自发邮件
        if 'self' in to_:
            to_.remove('self')
            to_.append(sender)
        to_ = set(to_)

    # 捕获意外情况
    if not (isinstance(to_, set) or isinstance(to_, list)):
        return False

    try:
        server.login(sender, password)
        for to in to_:
            try:
                message['To'] = Header("致<CampusDailyAutoSign>开发者", 'utf-8')  # 接收者
                server.sendmail(sender, to, message.as_string())
                logger.success("发送成功->{}".format(to))
            except smtplib.SMTPRecipientsRefused:
                logger.warning('邮箱填写错误或不存在->{}'.format(to))
            except smtplib.SMTPAuthenticationError:
                logger.error("授权码已更新")
                # aim_server("HKX-邮件发送脚本出错", '授权码已更新')
            except Exception as e:
                logger.error('>>> 发送失败 || {}'.format(e))
    finally:
        server.quit()
