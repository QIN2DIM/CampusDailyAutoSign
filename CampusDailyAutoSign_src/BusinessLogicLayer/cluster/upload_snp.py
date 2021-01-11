__all__ = ['UploadScreenshot']

import requests


class UploadScreenshot(object):
    def __init__(self):
        self.api_ = 'http://twqd.yaoqinse.com:6577/cpds/api/stu_twqd2'

    def run(self, user):
        requests.post(self.api_, data=user)
