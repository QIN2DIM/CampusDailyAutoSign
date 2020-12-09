__all__ = ['send_email']

import smtplib
from email.header import Header
from email.mime.text import MIMEText

from config import SMTP_ACCOUNT, logger


# 邮件发送模块
def send_email(msg, to, headers=None):
    """
    写死管理者账号，群发邮件
    :param msg: 正文内容
    :param to: 发送对象
    :param headers:
    :return:
    """
    headers = headers if headers else '<今日校园>打卡情况推送'
    sender = SMTP_ACCOUNT.get('email')
    password = SMTP_ACCOUNT.get('sid')
    smtp_server = 'smtp.qq.com'

    if to != '':
        message = MIMEText(msg, 'plain', 'utf-8')
        message['From'] = Header('ARAI.DM', 'utf-8')  # 发送者
        message['To'] = Header(to, 'utf-8')  # 接收者
        message['Subject'] = Header(f"{headers}", 'utf-8')
        server = smtplib.SMTP_SSL(smtp_server, 465)
        try:
            server.login(sender, password)
            server.sendmail(sender, to, message.as_string())
            logger.success("发送成功->{}".format(to))
            return True
        except smtplib.SMTPRecipientsRefused:
            logger.warning('邮箱填写错误或不存在->{}'.format(to))
            return False
        except Exception as e:
            logger.error('>>> 发送失败 || {}'.format(e))
            return False
        finally:
            server.quit()
