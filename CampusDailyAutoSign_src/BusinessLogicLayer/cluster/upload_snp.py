__all__ = ['UploadScreenshot']

import requests
from config import logger


class UploadScreenshot(object):
    def __init__(self):
        # your ip port 
        self.api_ = 'http://127.0.0.1:6577/cpds/api/stu_twqd2'

    def run(self, user):
        resp = requests.post(self.api_, data=user)
        response = resp.json()
        if response.get("code") == 300:
            logger.success(f'{response.get("username")} -- {response.get("info")}')
        else:
            logger.success(f'{response.get("username")} -- {response.get("info")}')
