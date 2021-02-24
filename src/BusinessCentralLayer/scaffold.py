from gevent import monkey

monkey.patch_all()
import gevent
from sys import argv
from typing import List
from src.BusinessCentralLayer.setting import *

_command_set = {

    # ---------------------------------------------
    # 部署接口
    # ---------------------------------------------
    'deploy': "部署项目（定时任务/Flask 开启与否取决于yaml配置文件）",
    # ---------------------------------------------
    # 调试接口
    # ---------------------------------------------
    # "*": "为在库用户立即执行一次签到任务(General)",
    # "-": "为在库用户立即执行一次签到任务(UploadSnp)并上传签到截图",
    "ping": "测试接口可用性",
    "sign [StuNumbers]": "为某个/一系列账号签到（立即执行）",
    "group": "为config.yaml group中的账号越权签到(General)",
    # ---------------------------------------------
    # 调用示例
    # ---------------------------------------------
    "example": "调用示例，如 python main.py ping"
}


class _ConfigQuarantine(object):
    def __init__(self):

        self.root = [
            SERVER_DIR_DATABASE, SERVER_DIR_SCREENSHOT, SERVER_DIR_CACHE
        ]
        self.flag = False

    def set_up_file_tree(self, root):
        # 检查默认下载地址是否残缺 深度优先初始化系统文件
        for child_ in root:
            if not os.path.exists(child_):
                self.flag = True
                try:
                    # 初始化文件夹
                    if os.path.isdir(child_) or not os.path.splitext(child_)[-1]:
                        os.mkdir(child_)
                        logger.success(f"系统文件链接成功->{child_}")
                    # 初始化文件
                    else:
                        if child_ == SERVER_PATH_COOKIES:
                            try:
                                with open(child_, 'w', encoding='utf-8', newline='') as fpx:
                                    fpx.write("")
                                logger.success(f"系统文件链接成功->{child_}")
                            except Exception as ep:
                                logger.exception(f"Exception{child_}{ep}")
                except Exception as ep:
                    logger.exception(ep)

    @staticmethod
    def check_config():
        if not all(SMTP_SCKEY.values()):
            logger.warning('<ConfigQuarantine> 您未正确配置<通信邮箱>信息(SMTP_SCKEY)')
        # if not SERVER_CHAN_SCKEY:
        #     logger.warning("您未正确配置<Server酱>的SCKEY")
        if not all([MySQL_SETTING.get("host"), MySQL_SETTING.get("password")]):
            logger.error('<ConfigQuarantine> 您未正确配置<MySQL_SETTING> 请配置后重启项目！')
            exit()
        if not all([SDK_OSS_SCKEY.get("id"), SDK_OSS_SCKEY.get("bucket_name")]):
            logger.warning("您未正确配置<SDK_OSS_SCKEY> 本项目将无法正常启用截图上传功能")

    def run(self):
        try:
            if [cq for cq in reversed(self.root) if not os.path.exists(cq)]:
                logger.warning('系统文件残缺！')
                logger.debug("启动<工程重构>模块...")
                self.set_up_file_tree(self.root)
            self.check_config()

        finally:
            if self.flag:
                logger.success(">>> 运行环境链接完成，请重启项目")
                exec("if self.flag:\n\texit()")


_ConfigQuarantine().run()


class _ScaffoldGuider(object):
    # __slots__ = list(command_set.keys())

    def __init__(self):
        # 脚手架公开接口
        self.scaffold_ruler = [i for i in self.__dir__() if i.startswith('_scaffold_')]

    @logger.catch()
    def startup(self, driver_command_set: List[str]):
        """
        仅支持单进程使用
        @param driver_command_set: 在空指令时列表仅有1个元素，表示启动路径
        @return:
        """
        # logger.info(f">>> {' '.join(driver_command_set)}")

        # -------------------------------
        # TODO 优先级0：指令清洗
        # -------------------------------
        # CommandId or List[CommandId]
        driver_command: List[str] = []

        # 未输入任何指令 列出脚手架简介
        if len(driver_command_set) == 1:
            print("\n".join([f">>> {menu[0].ljust(30, '-')}|| {menu[-1]}" for menu in _command_set.items()]))
            return True

        # 输入立即指令 转译指令
        if len(driver_command_set) == 2:
            driver_command = [driver_command_set[-1].lower(), ]
        # 输入指令集 转译指令集
        elif len(driver_command_set) > 2:
            driver_command = list(set([command.lower() for command in driver_command_set[1:]]))

        # 捕获意料之外的情况
        if not isinstance(driver_command, list):
            return True
        # -------------------------------
        # TODO 优先级1：解析运行参数（主进程瞬发）
        # -------------------------------

        if "group" in driver_command:
            driver_command.remove('group')

            # 读取本机静态用户数据
            group_ = set(config_['group'])
            group_ = [{'username': j} for j in group_]
            self._scaffold_group(stu_numbers=group_)

        elif "sign" in driver_command:
            driver_command.remove('sign')

            # 将除`sign`外的所有数字元素都视为该指令的启动参数
            # 既该指令解析的账号仅能是数字码，不兼容别名
            student_numbers: list = driver_command.copy()
            for pc_ in reversed(student_numbers):
                try:
                    int(pc_)
                except ValueError:
                    student_numbers.remove(pc_)

            # 检查student_numbers是否为空指令
            if student_numbers.__len__() == 0:
                logger.error(f"<ScaffoldGuider> 参数缺失 'sign [StuNumber] or sign group' but not {driver_command}")
                return False
            else:
                group_ = [{'username': j} for j in student_numbers]
                return self._scaffold_group(stu_numbers=group_)

        # -------------------------------
        # TODO 优先级2：运行并发指令
        # -------------------------------
        task_list = []
        while driver_command.__len__() > 0:
            _pending_command = driver_command.pop()
            try:
                task_list.append(gevent.spawn(eval(f"self._scaffold_{_pending_command}")))
            except AttributeError:
                pass
            except Exception as e:
                logger.warning(f'未知错误 <{_pending_command}> {e}')
        else:
            # 并发执行以上指令
            gevent.joinall(task_list)

        # -------------------------------
        # TODO 优先级3：自定义参数部署（阻塞进程）
        # -------------------------------
        if 'deploy' in driver_command:
            self._scaffold_deploy()

    @staticmethod
    def _scaffold_deploy():
        from src.BusinessCentralLayer.middleware.interface_io import sei
        sei.startup_system()

    @staticmethod
    def _scaffold_group(stu_numbers: List[dict]):
        logger.info(f"<ScaffoldGuider>  StartupSignInGroup-debug || {stu_numbers}")
        from src.BusinessLogicLayer.apis.vulcan_ash import SignInSpeedup
        SignInSpeedup(task_docker=stu_numbers).interface()

    @staticmethod
    def _scaffold_ping():
        """
        测试校园网API是否正常
        :return:
        """

        import pycurl

        test_url = [
            'https://ehall.hainanu.edu.cn/jsonp/ywtb/searchServiceItem?flag=0',
            'https://ehall.hainanu.edu.cn/qljfwapp/sys/lwHainanuStuTempReport/*default/index.do#/stuTempReport'
        ]
        for url in test_url:
            c = pycurl.Curl()
            c.setopt(pycurl.URL, url)
            c.setopt(pycurl.CONNECTTIMEOUT, 5)
            c.setopt(pycurl.TIMEOUT, 5)
            c.setopt(pycurl.NOPROGRESS, 1)
            c.setopt(pycurl.FORBID_REUSE, 1)
            c.setopt(pycurl.MAXREDIRS, 1)
            c.setopt(pycurl.DNS_CACHE_TIMEOUT, 30)

            index_file = open(os.path.dirname(os.path.realpath(__file__)) + "/content.txt", "wb")
            c.setopt(pycurl.WRITEHEADER, index_file)
            c.setopt(pycurl.WRITEDATA, index_file)

            c.perform()  # 提交请求

            print("\n测试网站: ", url)
            print("HTTP状态码: {}".format(c.getinfo(c.HTTP_CODE)))
            print("DNS解析时间：{} ms".format(round(c.getinfo(c.NAMELOOKUP_TIME) * 1000), 2))
            print("建立连接时间：{} ms".format(round(c.getinfo(c.CONNECT_TIME) * 1000), 2))
            print("准备传输时间：{} ms".format(round(c.getinfo(c.PRETRANSFER_TIME) * 1000), 2))
            print("传输开始时间：{} ms".format(round(c.getinfo(c.STARTTRANSFER_TIME) * 1000), 2))
            print("传输结束总时间：{} ms".format(round(c.getinfo(c.TOTAL_TIME) * 1000), 2))
            c.close()


scaffold = _ScaffoldGuider()
if __name__ == '__main__':
    print(scaffold.scaffold_ruler)
    scaffold.startup(argv)
