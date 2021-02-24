__all__ = ['lsu_']

import os
from typing import List, Dict

import gevent
from gevent.queue import Queue

from src.BusinessCentralLayer.setting import logger


class _LightweightSpeedup(object):
    """轻量化的协程控件"""

    def __init__(self, work_q: Queue = Queue(), task_docker=None, power: int = os.cpu_count()):
        self.work_q = work_q
        self.task_docker = task_docker
        self.power = power
        self.temp_cache: Dict[str:int] = {}
        self.apollo: List[List[str]] = []

    def launch(self):
        while not self.work_q.empty():
            task = self.work_q.get_nowait()
            self.control_driver(task)

    @staticmethod
    def beat_sync(sleep_time: float):
        gevent.sleep(sleep_time)

    def control_driver(self, user):
        """
        rewrite this method
        @param user:
        @return:
        """

    def offload_task(self):
        """

        @return:
        """

    def killer(self):
        """

        @return:
        """
        pass

    def interface(self, power: int = os.cpu_count()) -> None:
        """

        @param power: 协程功率
        @return:
        """

        # logger.info(f"<Gevent> Atomic ash go! || <{self.__class__.__name__}>")

        # 任务重载
        self.offload_task()

        # 任务启动
        task_list = []

        # 性能释放校准
        power_ = self.power if self.power else power
        power_ = self.work_q.qsize() if power_ > self.work_q.qsize() else power_

        logger.info(f"<Gevent> power:{power_} qsize:{self.work_q.qsize()} || <{self.__class__.__name__}>")

        for x in range(power_):
            task = gevent.spawn(self.launch)
            task_list.append(task)
        gevent.joinall(task_list)

        # 性能回收
        self.killer()

        logger.success(f'<Gevent> MissionCompleted || <{self.__class__.__name__}>')


lsu_ = _LightweightSpeedup
