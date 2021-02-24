__all__ = ['df', 'sync_user_data', 'AliyunOSS']

from datetime import datetime
from typing import List, Tuple

import oss2
import pymysql

from src.BusinessCentralLayer.setting import MySQL_SETTING, logger, SDK_OSS_SCKEY, TIME_ZONE_CN, SERVER_DIR_SCREENSHOT


class _DataFlower(object):
    def __init__(self):
        self.table_name = ['user', ]

        self.conn, self.cursor = self.__prepare__(MySQL_SETTING)

        self.__init_tables__()

    def __prepare__(self, flower_config: dict) -> Tuple[pymysql.connections.Connection, pymysql.cursors.Cursor]:
        _conn = pymysql.connect(
            host=flower_config['host'],
            user=flower_config['user'],
            passwd=flower_config['password'],
            db=flower_config['db'])
        _cursor = _conn.cursor()

        return _conn, _cursor

    def __init_tables__(self):
        for table_name in self.table_name:
            if table_name == 'user':
                sql = f'CREATE TABLE IF NOT EXISTS {table_name} (' \
                      'username VARCHAR(255) NOT NULL PRIMARY KEY,' \
                      'password VARCHAR(255) NOT NULL,' \
                      'email VARCHAR(100) NOT NULL,' \
                      'cookie VARCHAR(100))'

                self.cursor.execute(sql)

    def __fetch_user__(self, username: str, tag_name: str or List[str]) -> None or Tuple[Tuple[str, ...]]:
        """
        查询用户表,不应直接调用此函数
        :param tag_name:
        :return:
        """
        if isinstance(tag_name, list):
            tag_name = ",".join(tag_name)
        try:
            sql = f'SELECT {tag_name} FROM user WHERE username = %s'
            na = (username,)
            self.cursor.execute(sql, na)
            return self.cursor.fetchall()
        finally:
            self.conn.close()

    def upload_table(self):
        pass

    def add_user(self, user: dict or List[dict]):
        """
        添加用户，表名 user
        :param user: 传入学号 密码 邮箱，可传入多个用户
        :return:
        """

        if isinstance(user, dict):
            user = [user, ]
        elif not isinstance(user, list):
            logger.warning('MySQL add_user 调用格式有误')

        try:
            for user_ in user:
                try:
                    sql = f'INSERT INTO user (username, password, email) VALUES (%s, %s, %s)'
                    val = (user_["username"], user_['password'], user_['email'])
                    self.cursor.execute(sql, val)
                except KeyError as e:
                    logger.warning(f"MySQL数据解析出错，user:dict必须同时包含username、password以及email的键值对{e}")
                    # return 702
                except pymysql.err.IntegrityError as e:
                    logger.warning(f'{user_["username"]} -- 用户已在库，若需修改用户信息，请使用更新指令{e}')
                    # return 701
                else:
                    logger.success(f'{user_["username"]} -- 用户添加成功')
                    # return 700
        finally:
            self.conn.commit()
            self.conn.close()

    def del_user(self, username: str):
        result = _DataFlower().is_user(username)
        try:
            sql = f'DELETE FROM user WHERE username = %s'
            na = (username,)
            self.cursor.execute(sql, na)
            if result:
                logger.success(f'{username} -- 删除成功')
        finally:
            self.conn.commit()
            self.conn.close()

    def update_user(self, username: str, modify_items: dict):
        """

        :param username:用户名，用于定位
        :param modify_items:{修改项：修改值}
        :return:
        """

        try:
            for item in modify_items.items():
                if item[0] != 'username':
                    sql = f'UPDATE user SET {item[0]} = %s WHERE username = %s'
                    na = (item[1], username)
                    self.cursor.execute(sql, na)
        except pymysql.err.OperationalError as e:
            logger.warning(f"{username} -- 修改的键目标不存在 {e}")
        else:
            logger.success(f'{username} -- 数据修改成功')
        finally:
            self.conn.commit()
            self.conn.close()

    def is_user(self, username: str) -> bool:
        """
        通过该函数判断用户是否在库
        :param username:
        :return: True在库 False 不在
        """

        if isinstance(username, str):
            result = self.__fetch_user__(username, tag_name=username)
            if result:
                logger.info(f'{username} -- 用户在库')
                return True
            else:
                logger.info(f'{username} -- 用户不存在')
                return False

    def load_all_user_data(self):
        try:
            sql = f'SELECT username, password, email, cookie FROM user'
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        finally:
            self.conn.close()


class AliyunOSS(object):

    def __init__(self):
        access_key_id = SDK_OSS_SCKEY['id']
        access_key_secret = SDK_OSS_SCKEY['secret']
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket_name = SDK_OSS_SCKEY['bucket_name']
        self.bucket = oss2.Bucket(auth, SDK_OSS_SCKEY['endpoint'], bucket_name)

        self.osh_day = str(datetime.now(TIME_ZONE_CN)).split(" ")[0]
        self.root_obj = f'cpds/api/stu_snp/{self.osh_day}/'

    def upload_base64(self, content: str, username: str):
        result = self.bucket.put_object(f'{self.root_obj}{username}.txt', content)

        # # HTTP返回码。
        # print('http status: {0}'.format(result.status))
        # # 请求ID。请求ID是请求的唯一标识，强烈建议在程序日志中添加此参数。
        # print('request_id: {0}'.format(result.request_id))
        # # ETag是put_object方法返回值特有的属性，用于标识一个Object的内容。
        # print('ETag: {0}'.format(result.etag))
        # # HTTP响应头部。
        # print('date: {0}'.format(result.headers['date']))

    def snp_exist(self, username):
        return self.bucket.object_exists(f'{self.root_obj}{username}.txt')

    def download_snp(self, username):
        if self.snp_exist(username):
            self.bucket.get_object_to_file(f'{self.root_obj}{username}.txt', SERVER_DIR_SCREENSHOT + f'/{username}.txt')
        else:
            return False


df = _DataFlower()


def sync_user_data() -> List[dict]:
    data = _DataFlower().load_all_user_data()
    users = [dict(zip(['username', 'password', 'email', 'cookie'], user)) for user in data]
    return users
