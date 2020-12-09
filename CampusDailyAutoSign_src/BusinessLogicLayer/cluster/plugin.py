__all__ = ['get_proxy']

import requests
from requests.exceptions import *


class ProxyGenerator(object):

    @staticmethod
    def get_proxy_ip() -> str:
        return requests.get('http://127.0.0.1:5555/random').text

    def generate_proxies(self, test_task: dict, retry=0):
        if retry >= 3:
            # print('重试{}次，获取失败，任务结束'.format(retry))
            return False
        try:
            proxies = {
                'http': test_task['ip'],
            }
            test_url = test_task['url']

            res = requests.get(test_url, proxies=proxies, timeout=1)
            res.raise_for_status()
            if res.status_code == 200:
                # print('>>> 代理获取成功 || {}'.format(proxies))
                return proxies
        except RequestException:
            retry += 1
            # print('代理超时，即将重试，重试次数{}'.format(retry))
            return self.generate_proxies(test_task, retry)

    # 模块接口
    def run(self) -> dict:
        task = {
            'ip': self.get_proxy_ip(),
            'url': 'https://www.baidu.com'
        }
        return self.generate_proxies(task)


def get_proxy() -> dict:
    return ProxyGenerator().run()


if __name__ == '__main__':
    print(get_proxy())
